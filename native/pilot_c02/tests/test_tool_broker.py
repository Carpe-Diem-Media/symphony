"""Direct offline regression tests for the bounded native tool broker."""
import fcntl
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import struct
import subprocess
import tempfile
import time
import unittest

NATIVE = Path(__file__).resolve().parents[1]
BROKER = NATIVE / "build/tool-broker"
RUNNER = NATIVE / "tests/run_attempt.py"
MAX_FRAME = 8192


def load_runner():
    spec = importlib.util.spec_from_file_location("broker_test_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_exact(fd, size, deadline):
    result = bytearray()
    while len(result) < size:
        left = deadline - time.monotonic()
        if left <= 0 or not select.select([fd], [], [], left)[0]:
            raise TimeoutError("broker reply deadline expired")
        chunk = os.read(fd, size - len(result))
        if not chunk:
            raise EOFError("broker reply pipe closed")
        result.extend(chunk)
    return bytes(result)


def read_frame(fd, deadline):
    size = struct.unpack(">I", read_exact(fd, 4, deadline))[0]
    if not 0 < size <= MAX_FRAME:
        raise AssertionError(f"invalid broker reply size: {size}")
    return json.loads(read_exact(fd, size, deadline))


def send_frame(fd, payload):
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    if not 0 < len(encoded) <= MAX_FRAME:
        raise AssertionError("test request exceeds broker frame limit")
    os.write(fd, struct.pack(">I", len(encoded)) + encoded)


class ToolBrokerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["make", "-C", str(NATIVE), "build/tool-broker"], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        cls.runner = load_runner()

    def make_permit(self, root, mode, content=None):
        workspace = root / "workspace"
        workspace.mkdir(mode=0o700)
        if content is None:
            content = b"First fixed fact.\nSecond fixed fact.\n" + b"planning detail\n" * 7
        (workspace / "planner_input.txt").write_bytes(content)
        (workspace / "README.md").write_text("Private broker fixture.\n")
        env = dict(self.runner.GIT_ENV)
        commands = [
            ["/usr/bin/git", "init", "-q"],
            ["/usr/bin/git", "add", "planner_input.txt", "README.md"],
            ["/usr/bin/git", "-c", "user.name=Broker Fixture", "-c", "user.email=broker@example.invalid",
             "commit", "-qm", "fixture"],
        ]
        for command in commands:
            subprocess.run(command, cwd=workspace, env=env, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        commit = subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"], cwd=workspace, env=env).decode().strip()
        tree = subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD^{tree}"], cwd=workspace, env=env).decode().strip()
        manifest = {
            "attempt": "broker-native-test-attempt", "binding": "a" * 64,
            "deadline_ms": int((time.monotonic() + 4.0) * 1000),
            "fault": "none", "holder_sha256": hashlib.sha256(BROKER.read_bytes()).hexdigest(),
            "context": {"workspace": str(workspace), "role": "Planner", "grant_id": "fixture-grant",
                        "source_commit": commit, "source_tree": tree, "context_digest": "0" * 64},
        }
        pipes = (*os.pipe2(os.O_CLOEXEC), *os.pipe2(os.O_CLOEXEC))
        self.runner.seal_broker_inputs(root, manifest, pipes, BROKER, mode)
        return pipes, manifest, content

    @staticmethod
    def launch(root, pipes):
        permit_bytes = (root / "broker-permit").read_bytes()
        permit_fd = os.memfd_create("broker-test-permit", os.MFD_ALLOW_SEALING | os.MFD_CLOEXEC)
        os.write(permit_fd, permit_bytes)
        fcntl.fcntl(permit_fd, fcntl.F_ADD_SEALS,
                    fcntl.F_SEAL_SEAL | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_GROW | fcntl.F_SEAL_WRITE)
        child_sources = [fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 10) for fd in (permit_fd, pipes[0], pipes[3])]
        pid = os.fork()
        if pid == 0:
            try:
                null = os.open("/dev/null", os.O_RDWR)
                os.dup2(null, 0); os.dup2(null, 1); os.dup2(null, 2)
                for source, target in zip(child_sources, (4, 5, 6)):
                    os.dup2(source, target, inheritable=True)
                os.closerange(7, 1 << 20)
                os.execve(BROKER, [str(BROKER)], {})
            except BaseException:
                os._exit(127)
        for fd in child_sources:
            os.close(fd)
        os.close(permit_fd)
        return pid

    @staticmethod
    def close_parent_endpoints(pipes):
        os.close(pipes[0])
        os.close(pipes[3])

    def prepare(self, root, mode, content=None):
        pipes, manifest, content = self.make_permit(root, mode, content)
        if mode == "run":
            fd = os.open(root / "broker-release", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd, b"release\n"); os.fsync(fd); os.close(fd)
        pid = self.launch(root, pipes)
        os.close(pipes[0]); os.close(pipes[3])
        lines = (root / "broker-permit").read_bytes().splitlines()
        common, start, stop = (json.loads(lines[index]) for index in (9, 10, 11))
        deadline = manifest["deadline_ms"] / 1000
        send_frame(pipes[1], start)
        return pipes, pid, content, common, start, stop, deadline

    def finish(self, pipes, pid):
        os.close(pipes[1])
        _, status = os.waitpid(pid, 0)
        os.close(pipes[2])
        return os.waitstatus_to_exitcode(status)

    def run_to_exit(self, mode):
        with tempfile.TemporaryDirectory(prefix="tool-broker-test-") as temp:
            root = Path(temp)
            pipes, pid, content, common, start, stop, deadline = self.prepare(root, mode)
            frames = []
            while not any(frame["operation"] == "STARTED" for frame in frames):
                frames.append(read_frame(pipes[2], deadline))
            self.assertEqual(frames[0]["operation"], "STARTED")
            if mode == "wait_for_stop":
                send_frame(pipes[1], stop)
            while not any(frame["operation"] == "EXIT" for frame in frames):
                frames.append(read_frame(pipes[2], deadline))
            if mode == "run":
                send_frame(pipes[1], stop)
            while not any(frame["operation"] == "STOP_CONFIRMED" for frame in frames):
                frames.append(read_frame(pipes[2], deadline))
            code = self.finish(pipes, pid)
            self.assertEqual(code, 0)
            output = b"".join(base64.b64decode(frame["data"], validate=True)
                              for frame in frames if frame["operation"] == "OUTPUT")
            self.assertEqual(output, b"".join(content.splitlines(keepends=True)[:8]) if mode == "run" else b"")
            self.assertEqual([frame["operation"] for frame in frames].count("STARTED"), 1)
            self.assertEqual([frame["operation"] for frame in frames].count("EXIT"), 1)
            self.assertEqual([frame["operation"] for frame in frames].count("STOP_CONFIRMED"), 1)
            self.assertEqual((root / "broker-start-consumed").stat().st_mode & 0o777, 0o600)
            events = [json.loads(line) for line in (root / "broker-events.jsonl").read_text().splitlines()]
            self.assertEqual(sum(event["state"] == "START_INTENT_DURABLE" for event in events), 1)
            self.assertTrue(all(event["helper_ppid"] > 1 and event["helper_start_ticks"] > 0 for event in events))
            if mode == "wait_for_stop":
                self.assertEqual(events[-1]["state"], "STOP_VERIFIED")
            return root

    def test_fixed_read_output_and_positive_stop(self):
        self.run_to_exit("run")

    def test_held_child_stops_before_command_exec(self):
        self.run_to_exit("wait_for_stop")

    def test_unknown_request_refuses_before_start_consumption(self):
        with tempfile.TemporaryDirectory(prefix="tool-broker-invalid-") as temp:
            root = Path(temp)
            pipes, _manifest, _content = self.make_permit(root, "run")
            pid = self.launch(root, pipes)
            os.close(pipes[0]); os.close(pipes[3])
            lines = (root / "broker-permit").read_bytes().splitlines()
            invalid = json.loads(lines[10]); invalid["selector"] = "unapproved"
            send_frame(pipes[1], invalid)
            refusal = read_frame(pipes[2], (time.monotonic() + 2.0))
            self.assertEqual(refusal["operation"], "REFUSED")
            self.assertEqual(refusal["reason"], "invalid_request")
            code = self.finish(pipes, pid)
            self.assertNotEqual(code, 0)
            self.assertFalse((root / "broker-start-consumed").exists())
            self.assertFalse(any(json.loads(line)["state"] == "STARTED"
                                 for line in (root / "broker-events.jsonl").read_text().splitlines()))

    def test_changed_tracked_bytes_refuse_before_spawn(self):
        with tempfile.TemporaryDirectory(prefix="tool-broker-changed-") as temp:
            root = Path(temp)
            pipes, manifest, _ = self.make_permit(root, "run")
            (root / "workspace/planner_input.txt").write_text("different input\n")
            pid = self.launch(root, pipes)
            self.close_parent_endpoints(pipes)
            start = json.loads((root / "broker-permit").read_bytes().splitlines()[10])
            send_frame(pipes[1], start)
            reply = read_frame(pipes[2], manifest["deadline_ms"] / 1000)
            self.assertEqual(reply["operation"], "REFUSED")
            self.assertNotEqual(self.finish(pipes, pid), 0)
            self.assertFalse((root / "broker-start-consumed").exists())

    def test_output_limit_preserves_consumption_and_refuses_completion(self):
        with tempfile.TemporaryDirectory(prefix="tool-broker-output-limit-") as temp:
            root = Path(temp)
            pipes, pid, _, _, _, _, deadline = self.prepare(root, "run", b"x" * 32_768 + b"\n")
            seen = []
            while not seen or seen[-1]["operation"] != "REFUSED":
                seen.append(read_frame(pipes[2], deadline))
            self.assertEqual(self.finish(pipes, pid), 4)
            chunks = [base64.b64decode(frame["data"], validate=True)
                      for frame in seen if frame["operation"] == "OUTPUT"]
            self.assertTrue(chunks)
            self.assertTrue(all(len(chunk) <= 4096 for chunk in chunks))
            self.assertLessEqual(sum(map(len, chunks)), 16_384)
            self.assertFalse(any(frame["operation"] == "STOP_CONFIRMED" for frame in seen))
            self.assertTrue((root / "broker-start-consumed").is_file())

    def test_replayed_permit_cannot_fork_again(self):
        with tempfile.TemporaryDirectory(prefix="tool-broker-replay-") as temp:
            root = Path(temp)
            pipes, pid, _content, _common, _start, stop, deadline = self.prepare(root, "run")
            frames = []
            while not any(frame["operation"] == "EXIT" for frame in frames):
                frames.append(read_frame(pipes[2], deadline))
            send_frame(pipes[1], stop)
            while not any(frame["operation"] == "STOP_CONFIRMED" for frame in frames):
                frames.append(read_frame(pipes[2], deadline))
            self.assertEqual(self.finish(pipes, pid), 0)
            replay_pipes = (*os.pipe2(os.O_CLOEXEC), *os.pipe2(os.O_CLOEXEC))
            replay_pid = self.launch(root, replay_pipes)
            os.close(replay_pipes[0]); os.close(replay_pipes[3])
            start = json.loads((root / "broker-permit").read_bytes().splitlines()[10])
            send_frame(replay_pipes[1], start)
            reply = read_frame(replay_pipes[2], deadline)
            self.assertEqual(reply["operation"], "REFUSED")
            self.assertEqual(reply["reason"], "tool_uncertain")
            self.assertNotEqual(self.finish(replay_pipes, replay_pid), 0)
            events = [json.loads(line) for line in (root / "broker-events.jsonl").read_text().splitlines()]
            self.assertEqual(sum(event["state"] == "START_INTENT_DURABLE" for event in events), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
