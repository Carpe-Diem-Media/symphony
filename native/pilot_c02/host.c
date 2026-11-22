/* Real native synthetic materialization owner. Never accepts operational access material. */
#include "common.h"

static int durable_receipt(const char *name, const char *bytes, size_t size) {
    int fd = openat(root_fd, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) return -1;
    struct stat st;
    bool ok = !fstat(fd, &st) && S_ISREG(st.st_mode) && st.st_nlink == 1 &&
              st.st_uid == geteuid() && (st.st_mode & 0777) == 0600 &&
              write(fd, bytes, size) == (ssize_t)size && !fsync(fd) && !fsync(root_fd);
    close(fd);
    return ok ? 0 : -1;
}

static int write_ready_receipt(pid_t holder, unsigned long long holder_start) {
    char bytes[1024];
    int size = snprintf(bytes, sizeof(bytes),
        "{\"attempt\":\"%s\",\"binding\":\"%s\",\"context_digest\":\"%s\",\"fixture_sha256\":\"%s\",\"guard_pid\":%d,\"guard_start_ticks\":%llu,\"holder_pid\":%d,\"holder_start_ticks\":%llu,\"kind\":\"native-ready\",\"nonce\":\"%s\",\"scope\":\"SYNTHETIC_PIPE\",\"sequence\":0}",
        authority.attempt, authority.binding, authority.context_digest, authority.provider_fixture,
        authority.guard_pid, authority.guard_start, holder, holder_start,
        authority.provider_nonce);
    return size > 0 && (size_t)size < sizeof(bytes) ?
        durable_receipt("functional-ready.json", bytes, (size_t)size) : -1;
}

static int write_stop_receipt(pid_t holder, unsigned long long holder_start,
                              const char *journal_sha256) {
    pid_t host_parent = 0;
    unsigned long long host_start = 0;
    char bytes[1536];
    if (proc_identity(getpid(), &host_parent, &host_start)) return -1;
    int size = snprintf(bytes, sizeof(bytes),
        "{\"attempt\":\"%s\",\"binding\":\"%s\",\"context_digest\":\"%s\",\"disposal_verified\":true,\"fixture_sha256\":\"%s\",\"guard_pid\":%d,\"guard_start_ticks\":%llu,\"holder_pid\":%d,\"holder_start_ticks\":%llu,\"host_pid\":%d,\"host_start_ticks\":%llu,\"journal_sha256\":\"%s\",\"kind\":\"native-stopped\",\"nonce\":\"%s\",\"scope\":\"SYNTHETIC_PIPE\",\"sequence\":1,\"termination_observed\":true}",
        authority.attempt, authority.binding, authority.context_digest, authority.provider_fixture,
        authority.guard_pid, authority.guard_start, holder, holder_start, getpid(), host_start,
        journal_sha256, authority.provider_nonce);
    return size > 0 && (size_t)size < sizeof(bytes) ?
        durable_receipt("functional-stop.json", bytes, (size_t)size) : -1;
}

static bool fixture_matches(const char *path, const char *expected) {
    struct stat st;
    char actual[65];
    return path && !lstat(path, &st) && S_ISREG(st.st_mode) && !S_ISLNK(st.st_mode) &&
           !digest_path(path, actual) && !strcmp(actual, expected);
}

static int identity_matches(pid_t peer) {
    pid_t parent = 0, guard_parent = 0;
    unsigned long long start = 0, guard_start = 0;
    char path[128], digest[65];
    if (proc_identity(peer, &parent, &start) || parent != authority.guard_pid ||
        proc_identity(parent, &guard_parent, &guard_start) || guard_start != authority.guard_start) return -1;
    snprintf(path, sizeof(path), "/proc/%d/exe", peer);
    if (digest_path(path, digest) || strcmp(digest, authority.guard)) return -1;
    snprintf(path, sizeof(path), "/proc/%d/fd/3", peer);
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    int seals = fcntl(fd, F_GET_SEALS);
    int r = digest_fd(fd, digest);
    close(fd);
    if (r || strcmp(digest, authority.holder) || (seals & (F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL)) !=
        (F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL)) return -1;
    const char *names[] = {"pid", "user", "mnt", "net"};
    for (size_t i = 0; i < 4; i++) {
        struct stat child_ns, guard_ns;
        snprintf(path, sizeof(path), "/proc/%d/ns/%s", peer, names[i]);
        if (stat(path, &child_ns)) return -1;
        snprintf(path, sizeof(path), "/proc/%d/ns/%s", parent, names[i]);
        if (stat(path, &guard_ns) || child_ns.st_ino != guard_ns.st_ino || child_ns.st_dev != guard_ns.st_dev) return -1;
    }
    /* This comparison proves a selected synthetic topology, not qualified UID/LSM isolation. */
    char child_cgroup[65], guard_cgroup[65];
    snprintf(path, sizeof(path), "/proc/%d/cgroup", peer);
    if (digest_path(path, child_cgroup)) return -1;
    snprintf(path, sizeof(path), "/proc/%d/cgroup", parent);
    if (digest_path(path, guard_cgroup) || strcmp(child_cgroup, guard_cgroup)) return -1;
    return 0;
}
int main(int argc, char **argv) {
    if ((argc != 5 && argc != 6) || !hex64(argv[3]) || !reference(argv[4]) ||
        (root_fd = open_root(argv[1])) < 0) return 80;
    struct rlimit core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core) || prctl(PR_SET_DUMPABLE, 0) || prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) return 80;
    const char *fault = argv[2];
    strcpy(authority.binding, argv[3]); strcpy(authority.attempt, argv[4]);
    signal(SIGPIPE, SIG_IGN);
    if (faccessat(root_fd, "consumed", F_OK, 0) == 0) { puts("REUSE_REFUSED"); return 0; }
    int server = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    struct sockaddr_un address;
    if (server < 0 || endpoint(argv[1], &address) || bind(server, (struct sockaddr *)&address, sizeof(address)) || listen(server, 1)) return 81;
    puts("HOST_LISTENING"); fflush(stdout);
    unsigned long long startup_deadline = monotonic_ms() + 5000;
    if (!wait_fd(server, POLLIN, startup_deadline)) { event("QUARANTINED", 0); return 0; }
    int channel = accept4(server, NULL, NULL, SOCK_CLOEXEC);
    close(server); /* No second connection can be served. */
    struct ucred peer;
    socklen_t peer_size = sizeof(peer);
    struct request request;
    memset(&request, 0, sizeof(request));
    if (channel < 0 || read_permit() || strcmp(authority.binding, argv[3]) || strcmp(authority.attempt, argv[4]) ||
        ((authority.provider_nonce[0] != '\0') != (argc == 6) || (argc == 6 &&
          !fixture_matches(argv[5], authority.provider_fixture))) ||
        getsockopt(channel, SOL_SOCKET, SO_PEERCRED, &peer, &peer_size) ||
        peer_size != sizeof(peer) || peer.uid != geteuid() || peer.gid != getegid() ||
        !wait_fd(channel, POLLIN, authority.deadline) || receive_plain(channel, &request, sizeof(request)) != sizeof(request) ||
        memchr(request.binding, 0, sizeof(request.binding)) == NULL || memchr(request.attempt, 0, sizeof(request.attempt)) == NULL ||
        memchr(request.holder, 0, sizeof(request.holder)) == NULL || strcmp(request.binding, authority.binding) ||
        strcmp(request.attempt, authority.attempt) || strcmp(request.holder, authority.holder) || identity_matches(peer.pid)) {
        if (channel >= 0) close(channel);
        event("HOST_PERMISSION_REFUSED", 0); return 0;
    }
    int pidfd = (int)syscall(SYS_pidfd_open, peer.pid, 0);
    if (pidfd < 0 || marker("consumed")) { close(channel); event("QUARANTINED", peer.pid); return 0; }
    if (!strcmp(fault, "journal_failure") || event("MATERIALIZATION_INTENT", peer.pid)) {
        close(channel); event("QUARANTINED", peer.pid); close(pidfd); return 0;
    }
    if (send(channel, "V", 1, MSG_NOSIGNAL) != 1 || !wait_fd(channel, POLLIN, authority.deadline)) {
        close(channel); event("QUARANTINED", peer.pid); close(pidfd); return 0;
    }
    char protected_ack = 0;
    if (receive_plain(channel, &protected_ack, 1) != 1 || protected_ack != 'P' ||
        wait_fd(pidfd, POLLIN, monotonic_ms() + 1)) {
        close(channel); event("QUARANTINED", peer.pid); close(pidfd); return 0;
    }
    /* Material is generated only here, after the verified child exists. */
    unsigned char random[16];
    char synthetic[64] = "SYNTHETIC-NONLIVE-";
    if (getrandom(random, sizeof(random), 0) != sizeof(random)) { close(channel); event("QUARANTINED", peer.pid); return 0; }
    for (size_t i = 0; i < sizeof(random); i++) snprintf(synthetic + 18 + i * 2, 3, "%02x", random[i]);
    size_t size = strlen(synthetic) + 1;
    bool partial = !strcmp(fault, "partial_materialization");
    ssize_t sent = send(channel, synthetic, partial ? 8 : size, MSG_NOSIGNAL);
    explicit_bzero(synthetic, sizeof(synthetic)); explicit_bzero(random, sizeof(random));
    int recorded = !strcmp(fault, "post_materialization_journal_failure") ? -1 :
        event(partial || sent != (ssize_t)size ? "MATERIALIZATION_AMBIGUOUS" : "SYNTHETIC_MATERIALIZED", peer.pid);
    if (recorded) {
        /* Delivery may have happened. Keep consumed, stop only this pidfd and
         * never promote missing durable observations to disposal success. */
        close(channel);
        syscall(SYS_pidfd_send_signal, pidfd, SIGKILL, NULL, 0);
        if (wait_fd(pidfd, POLLIN, authority.deadline)) event("TERMINATION_VERIFIED", peer.pid);
        event("QUARANTINED", peer.pid);
        close(pidfd);
        return 0;
    }
    char extra;
    unsigned long long observed_holder_start = 0;
    if (wait_fd(channel, POLLIN | POLLHUP, authority.deadline) && receive_plain(channel, &extra, 1) == 0) {
        if (!event("CREDENTIAL_CHANNEL_CLOSED", peer.pid) && !marker("channel-closed") &&
            authority.provider_nonce[0]) {
            pid_t holder_parent = 0;
            if (proc_identity(peer.pid, &holder_parent, &observed_holder_start) ||
                holder_parent != authority.guard_pid || write_ready_receipt(peer.pid, observed_holder_start) ||
                event("FUNCTIONAL_READY_RECEIPT_WRITTEN", peer.pid))
                event("QUARANTINED", peer.pid);
        }
    }
    close(channel);
    if (strcmp(fault, "observe_failure") && wait_fd(pidfd, POLLIN, authority.deadline)) {
        if (!event("TERMINATION_VERIFIED", peer.pid)) {
            if (!strcmp(fault, "cleanup_failure")) event("QUARANTINED", peer.pid);
            else {
                while (faccessat(root_fd, "guard-reaped", F_OK, 0) && monotonic_ms() < authority.deadline) usleep(1000);
                bool schema2 = !strcmp(authority.profile, SCHEMA2_PROFILE);
                const char *terminal = schema2 ? "schema2-clean-exit" : "controlled-refusal";
                if (faccessat(root_fd, "guard-reaped", F_OK, 0) == 0 &&
                    (!schema2 || faccessat(root_fd, "channel-closed", F_OK, 0) == 0) &&
                    faccessat(root_fd, terminal, F_OK, 0) == 0) {
                    if (!event("DISPOSAL_VERIFIED", peer.pid) && !marker("disposed") &&
                        authority.provider_nonce[0]) {
                        char journal_sha256[65];
                        if (event("FUNCTIONAL_STOP_RECEIPT_WRITTEN", peer.pid) ||
                            digest_path("events.jsonl", journal_sha256) ||
                            write_stop_receipt(peer.pid, observed_holder_start, journal_sha256))
                            event("QUARANTINED", peer.pid);
                    }
                } else event("QUARANTINED", peer.pid);
            }
        }
    } else event("QUARANTINED", peer.pid);
    close(pidfd);
    return 0;
}
