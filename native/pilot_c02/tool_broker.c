#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <limits.h>
#include <arpa/inet.h>
#include <dirent.h>
#include <openssl/evp.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define MAX_FRAME 8192u
#define MAX_CHUNK 4096u
#define MAX_TOTAL 16384u
#define PERMIT_MAX 32768u
#define TOOL_MS 1000u
#define STOP_RESERVE_MS 200u

struct permit {
    unsigned long long deadline;
    char mode[24];
    char workspace[PATH_MAX];
    char journal[PATH_MAX];
    char file_sha[65];
    char shell_path[PATH_MAX];
    char shell_sha[65];
    char head_sha[65];
    char common[MAX_FRAME];
    char start[MAX_FRAME];
    char stop[MAX_FRAME];
};

static struct permit p;
static int journal_fd = -1;
static int journal_dir_fd = -1;
static unsigned long long operation_deadline;
static uint32_t seq_out = 1;
static pid_t child_pid = -1;
static pid_t child_group = -1;
static unsigned long long child_ticks;
static int child_pidfd = -1;
static char head_realpath[PATH_MAX];
static int child_status;
static bool stop_received;
static bool stop_verified;
static pid_t helper_ppid;
static pid_t helper_pid;
static unsigned long long helper_ticks;

static unsigned long long now_ms(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) _exit(90);
    return (unsigned long long)t.tv_sec * 1000u + (unsigned long long)t.tv_nsec / 1000000u;
}

static int read_full(int fd, void *buf, size_t n) {
    size_t off = 0;
    while (off < n) {
        ssize_t r = read(fd, (char *)buf + off, n - off);
        if (r < 0 && errno == EINTR) continue;
        if (r <= 0) return -1;
        off += (size_t)r;
    }
    return 0;
}

static int write_full(int fd, const void *buf, size_t n) {
    size_t off = 0;
    while (off < n) {
        ssize_t r = write(fd, (const char *)buf + off, n - off);
        if (r < 0 && errno == EINTR) continue;
        if (r <= 0) return -1;
        off += (size_t)r;
    }
    return 0;
}

static int wait_fd(int fd, short events, unsigned long long deadline) {
    for (;;) {
        unsigned long long now = now_ms();
        if (now >= deadline) return -1;
        struct pollfd pfd = {.fd=fd,.events=events};
        unsigned long long left = deadline - now;
        int timeout = left > INT_MAX ? INT_MAX : (int)left;
        int r = poll(&pfd, 1, timeout);
        if (r < 0 && errno == EINTR) continue;
        if (r <= 0 || (pfd.revents & (POLLERR|POLLNVAL))) return -1;
        if (pfd.revents & events) return 0;
        if (pfd.revents & POLLHUP) return -1;
    }
}

static int read_channel(void *buf, size_t n) {
    size_t off = 0;
    while (off < n) {
        ssize_t r = read(5, (char *)buf + off, n - off);
        if (r > 0) { off += (size_t)r; continue; }
        if (r < 0 && errno == EINTR) continue;
        if (r < 0 && (errno == EAGAIN || errno == EWOULDBLOCK) && !wait_fd(5, POLLIN, p.deadline)) continue;
        return -1;
    }
    return 0;
}

static int write_channel(const void *buf, size_t n) {
    size_t off = 0;
    while (off < n) {
        ssize_t r = write(6, (const char *)buf + off, n - off);
        if (r > 0) { off += (size_t)r; continue; }
        if (r < 0 && errno == EINTR) continue;
        if (r < 0 && (errno == EAGAIN || errno == EWOULDBLOCK) && !wait_fd(6, POLLOUT, p.deadline)) continue;
        return -1;
    }
    return 0;
}

static int valid_digest(const char *s) {
    if (strlen(s) != 64) return 0;
    for (size_t i = 0; i < 64; i++)
        if (!((s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'f'))) return 0;
    return 1;
}

static int digest_fd(int fd, char out[65]) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    unsigned char hash[32], buf[8192];
    unsigned int n = 0;
    int ok = ctx && lseek(fd, 0, SEEK_SET) >= 0 && EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) == 1;
    ssize_t r;
    while (ok && (r = read(fd, buf, sizeof(buf))) > 0)
        ok = EVP_DigestUpdate(ctx, buf, (size_t)r) == 1;
    if (!ok || r < 0 || EVP_DigestFinal_ex(ctx, hash, &n) != 1 || n != 32) ok = 0;
    EVP_MD_CTX_free(ctx);
    if (!ok) return -1;
    for (size_t i = 0; i < 32; i++) snprintf(out + i * 2, 3, "%02x", hash[i]);
    return 0;
}

static int hash_path(const char *path, const char *expected) {
    int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    struct stat st;
    char actual[65];
    if (fd < 0 || fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_uid != 0 ||
        (st.st_mode & 0022) != 0 || (st.st_mode & 0111) == 0 ||
        digest_fd(fd, actual) || strcmp(actual, expected)) { if (fd >= 0) close(fd); return -1; }
    close(fd);
    return 0;
}

static int trusted_ancestry(const char *path) {
    char current[PATH_MAX];
    size_t n = strlen(path);
    if (!n || n >= sizeof(current) || path[0] != '/') return -1;
    strcpy(current, path);
    for (char *slash = current + 1; ; slash++) {
        if (*slash != '/' && *slash != 0) continue;
        char saved = *slash; *slash = 0;
        struct stat st;
        if (stat(current, &st) || st.st_uid != 0 || (st.st_mode & 0022) != 0) return -1;
        *slash = saved;
        if (!saved) break;
    }
    return 0;
}

static int verify_head(const char *expected) {
    struct stat link_st;
    char resolved[PATH_MAX];
    if (lstat("/usr/bin/head", &link_st) || !S_ISLNK(link_st.st_mode) || link_st.st_uid != 0 ||
        !realpath("/usr/bin/head", resolved) || trusted_ancestry(resolved) || hash_path(resolved, expected)) return -1;
    if (head_realpath[0] && strcmp(head_realpath, resolved)) return -1;
    strcpy(head_realpath, resolved);
    return 0;
}

static int verify_selected_file(int workspace_fd, int held_fd, const struct stat *identity) {
    struct stat held, current;
    char hash[65];
    int current_fd = openat(workspace_fd, "planner_input.txt", O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    if (current_fd < 0 || fstat(held_fd, &held) || fstat(current_fd, &current) ||
        held.st_dev != identity->st_dev || held.st_ino != identity->st_ino ||
        current.st_dev != identity->st_dev || current.st_ino != identity->st_ino ||
        digest_fd(held_fd, hash) || strcmp(hash, p.file_sha)) {
        if (current_fd >= 0) close(current_fd);
        return -1;
    }
    close(current_fd);
    return 0;
}

static int read_permit(void) {
    struct stat st;
    int seals = fcntl(4, F_GET_SEALS);
    const int required = F_SEAL_SEAL | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE;
    if (seals < 0 || (seals & required) != required || fstat(4, &st) || !S_ISREG(st.st_mode) ||
        st.st_size <= 0 || st.st_size > PERMIT_MAX) return -1;
    char bytes[PERMIT_MAX + 1];
    if (lseek(4, 0, SEEK_SET) < 0 || read_full(4, bytes, (size_t)st.st_size)) return -1;
    bytes[st.st_size] = 0;
    close(4);
    FILE *f = fmemopen(bytes, (size_t)st.st_size, "r");
    if (!f) return -1;
    char line[PERMIT_MAX + 1];
    bool ok = fgets(line, sizeof(line), f) && !strcmp(line, "H100-BROKER-PERMIT-1\n");
    if (ok && fgets(line, sizeof(line), f)) {
        char *end = NULL; errno = 0; p.deadline = strtoull(line, &end, 10);
        ok = !errno && end != line && !strcmp(end, "\n");
    } else ok = false;
    if (ok && fgets(p.mode, sizeof(p.mode), f)) {
        size_t n = strlen(p.mode);
        ok = n > 1 && p.mode[n-1] == '\n';
        p.mode[n-1] = 0;
        ok = ok && (!strcmp(p.mode, "run") || !strcmp(p.mode, "wait_for_stop"));
    } else ok = false;
    if (ok) ok = fgets(p.workspace, sizeof(p.workspace), f) != NULL;
    if (ok) { size_t n = strlen(p.workspace); ok = n > 1 && p.workspace[n-1] == '\n'; p.workspace[n-1] = 0; }
    if (ok) ok = fgets(p.journal, sizeof(p.journal), f) != NULL;
    if (ok) { size_t n = strlen(p.journal); ok = n > 1 && p.journal[n-1] == '\n'; p.journal[n-1] = 0; }
    if (ok && fgets(line, sizeof(line), f)) { line[strcspn(line, "\n")] = 0; ok = valid_digest(line); if (ok) strcpy(p.file_sha, line); } else ok = false;
    if (ok) ok = fgets(p.shell_path, sizeof(p.shell_path), f) != NULL;
    if (ok) { size_t n = strlen(p.shell_path); ok = n > 1 && p.shell_path[n-1] == '\n'; p.shell_path[n-1] = 0; }
    if (ok && fgets(line, sizeof(line), f)) { line[strcspn(line, "\n")] = 0; ok = valid_digest(line); if (ok) strcpy(p.shell_sha, line); } else ok = false;
    if (ok && fgets(line, sizeof(line), f)) { line[strcspn(line, "\n")] = 0; ok = valid_digest(line); if (ok) strcpy(p.head_sha, line); } else ok = false;
    if (ok) ok = fgets(p.common, sizeof(p.common), f) != NULL;
    if (ok) { size_t n = strlen(p.common); ok = n > 1 && p.common[n-1] == '\n'; p.common[n-1] = 0; }
    if (ok) ok = fgets(p.start, sizeof(p.start), f) != NULL;
    if (ok) { size_t n = strlen(p.start); ok = n > 1 && p.start[n-1] == '\n'; p.start[n-1] = 0; }
    if (ok) ok = fgets(p.stop, sizeof(p.stop), f) != NULL;
    if (ok) { size_t n = strlen(p.stop); ok = n > 1 && p.stop[n-1] == '\n'; p.stop[n-1] = 0; }
    int extra = fgetc(f);
    fclose(f);
    if (!ok || extra != EOF || p.deadline <= now_ms() || p.workspace[0] != '/' || p.journal[0] != '/' ||
        p.shell_path[0] != '/' || strcmp(p.shell_path, "/usr/bin/dash") ||
        p.common[0] != '{' || p.common[strlen(p.common)-1] != '}' ||
        p.start[0] != '{' || p.stop[0] != '{') return -1;
    return 0;
}

static int validate_channels(void) {
    struct stat in, out;
    int in_flags = fcntl(5, F_GETFL), out_flags = fcntl(6, F_GETFL);
    if (in_flags < 0 || out_flags < 0 || (in_flags & O_ACCMODE) != O_RDONLY ||
        (out_flags & O_ACCMODE) != O_WRONLY || fstat(5, &in) || fstat(6, &out) ||
        !S_ISFIFO(in.st_mode) || !S_ISFIFO(out.st_mode) ||
        fcntl(5, F_SETFL, in_flags | O_NONBLOCK) || fcntl(6, F_SETFL, out_flags | O_NONBLOCK)) return -1;
    return 0;
}

static int journal(const char *state) {
    char record[640];
    int n = snprintf(record, sizeof(record), "{\"state\":\"%s\",\"pid\":%ld,\"start_ticks\":%llu,\"helper_pid\":%ld,\"helper_ppid\":%ld,\"helper_start_ticks\":%llu,\"at_ms\":%llu}\n",
        state, (long)child_pid, child_ticks, (long)getpid(), (long)helper_ppid, helper_ticks, now_ms());
    if (n <= 0 || (size_t)n >= sizeof(record) || flock(journal_fd, LOCK_EX)) return -1;
    int ok = write_full(journal_fd, record, (size_t)n) == 0 && fsync(journal_fd) == 0;
    flock(journal_fd, LOCK_UN);
    return ok ? 0 : -1;
}

static int consume_marker(const char *name, const void *bytes, size_t n) {
    int fd = openat(journal_dir_fd, name, O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC|O_NOFOLLOW, 0600);
    if (fd < 0) return -1;
    struct stat st;
    int ok = fstat(fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_nlink == 1 &&
             st.st_uid == geteuid() && (st.st_mode & 0777) == 0600 &&
             write_full(fd, bytes, n) == 0 && fsync(fd) == 0 && fsync(journal_dir_fd) == 0;
    close(fd);
    return ok ? 0 : -1;
}

static int send_frame(const char *extra) {
    char payload[MAX_FRAME];
    size_t ncommon = strlen(p.common);
    if (ncommon < 2 || p.common[ncommon-1] != '}') return -1;
    int n = snprintf(payload, sizeof(payload), "%.*s,%s}", (int)ncommon - 1, p.common, extra);
    if (n <= 0 || (size_t)n > MAX_FRAME) return -1;
    uint32_t be = htonl((uint32_t)n);
    return write_channel(&be, sizeof(be)) || write_channel(payload, (size_t)n) ? -1 : 0;
}

static unsigned long long proc_start_ticks(pid_t pid) {
    char path[64], buf[4096];
    snprintf(path, sizeof(path), "/proc/%ld/stat", (long)pid);
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return 0;
    ssize_t n = read(fd, buf, sizeof(buf)-1); close(fd);
    if (n <= 0) return 0;
    buf[n] = 0;
    char *q = strrchr(buf, ')');
    if (!q || q[1] != ' ') return 0;
    char *save = NULL, *tok = strtok_r(q + 2, " ", &save);
    for (int field = 3; tok; field++, tok = strtok_r(NULL, " ", &save))
        if (field == 22) return strtoull(tok, NULL, 10);
    return 0;
}

static int proc_group_id(pid_t pid, pid_t *group) {
    char path[64], buf[4096];
    snprintf(path, sizeof(path), "/proc/%ld/stat", (long)pid);
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    ssize_t n = read(fd, buf, sizeof(buf)-1); close(fd);
    if (n <= 0) return -1;
    buf[n] = 0;
    char *q = strrchr(buf, ')');
    if (!q || q[1] != ' ') return -1;
    char *save = NULL, *tok = strtok_r(q + 2, " ", &save);
    for (int field = 3; tok; field++, tok = strtok_r(NULL, " ", &save))
        if (field == 5) { *group = (pid_t)strtol(tok, NULL, 10); return 0; }
    return -1;
}

static int other_group_members(pid_t group, pid_t leader) {
    DIR *proc = opendir("/proc");
    if (!proc) return -1;
    int count = 0;
    struct dirent *entry;
    while ((entry = readdir(proc)) != NULL) {
        char *end = NULL;
        errno = 0;
        long raw = strtol(entry->d_name, &end, 10);
        if (errno || end == entry->d_name || *end || raw <= 0 || raw == leader) continue;
        pid_t found_group;
        if (proc_group_id((pid_t)raw, &found_group)) {
            if (errno == ENOENT || errno == ESRCH) continue;
            closedir(proc);
            return -1;
        }
        if (found_group == group) count++;
    }
    closedir(proc);
    return count;
}

static int observe_child_exit(void) {
    siginfo_t info;
    memset(&info, 0, sizeof(info));
    if (child_pidfd < 0 || waitid(P_PIDFD, (id_t)child_pidfd, &info, WEXITED|WNOWAIT|WNOHANG)) return -1;
    if (!info.si_pid) return 0;
    child_status = info.si_code == CLD_EXITED ? info.si_status << 8 : (info.si_status & 0x7f);
    return 1;
}

static int signal_owned_group(int signo) {
    if (child_pid <= 0 || child_group != child_pid || getpgid(child_pid) != child_group) return -1;
    return kill(-child_group, signo) == 0 || errno == ESRCH ? 0 : -1;
}

static int install_tool_syscall_filter(void) {
    struct sock_filter code[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, (unsigned int)offsetof(struct seccomp_data, arch)),
#if defined(__x86_64__)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
#elif defined(__aarch64__)
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_AARCH64, 1, 0),
#else
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
#endif
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, (unsigned int)offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_socket, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_socketpair, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog program = {.len=(unsigned short)(sizeof(code)/sizeof(code[0])),.filter=code};
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) ||
        prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program)) return -1;
    return 0;
}

static int receive_expected(const char *expected) {
    uint32_t be, len;
    if (read_channel(&be, sizeof(be))) return -1;
    len = ntohl(be);
    if (!len || len > MAX_FRAME) return -1;
    char buf[MAX_FRAME + 1];
    if (read_channel(buf, len)) return -1;
    buf[len] = 0;
    return strlen(expected) == len && !memcmp(buf, expected, len) ? 0 : -1;
}

static int emit_output(int stream, const unsigned char *data, size_t n) {
    unsigned char encoded[4 * ((MAX_CHUNK + 2) / 3) + 1];
    if (n > MAX_CHUNK || EVP_EncodeBlock(encoded, data, (int)n) < 0) return -1;
    char extra[6000];
    int k = snprintf(extra, sizeof(extra), "\"operation\":\"OUTPUT\",\"sequence\":%u,\"stream\":\"%s\",\"data\":\"%s\"",
        seq_out++, stream == 0 ? "stdout" : "stderr", encoded);
    return k <= 0 || (size_t)k >= sizeof(extra) ? -1 : send_frame(extra);
}

static int stop_child(void) {
    if (child_pid <= 0 || child_group != child_pid || child_ticks == 0) return -1;
    if (child_pidfd < 0 || getpgid(child_pid) != child_group) return -1;
    int exited = observe_child_exit();
    if (exited < 0) return -1;
    int members = other_group_members(child_group, child_pid);
    if (members < 0) return -1;
    if (!exited || members > 0) {
        if (signal_owned_group(SIGTERM)) return -1;
        for (int i = 0; i < 20 && now_ms() < p.deadline; i++) {
            exited = observe_child_exit();
            members = other_group_members(child_group, child_pid);
            if (exited < 0 || members < 0) return -1;
            if (exited && members == 0) break;
            poll(NULL, 0, 10);
        }
        if (!exited || members > 0) {
            if (signal_owned_group(SIGKILL)) return -1;
            for (int i = 0; i < 20 && now_ms() < p.deadline; i++) {
                exited = observe_child_exit();
                members = other_group_members(child_group, child_pid);
                if (exited < 0 || members < 0) return -1;
                if (exited && members == 0) break;
                poll(NULL, 0, 10);
            }
        }
    }
    if (exited != 1 || members != 0 || getpgid(child_pid) != child_group) return -1;
    int status = 0;
    if (waitpid(child_pid, &status, 0) != child_pid) return -1;
    child_status = status;
    struct pollfd pfd = {.fd=child_pidfd,.events=POLLIN};
    if (poll(&pfd, 1, 0) <= 0 || !(pfd.revents & POLLIN)) return -1;
    if (other_group_members(child_group, child_pid) != 0) return -1;
    stop_verified = true;
    return 0;
}

static int send_exit(void) {
    int exit_code = WIFEXITED(child_status) ? WEXITSTATUS(child_status) :
                    (WIFSIGNALED(child_status) ? 128 + WTERMSIG(child_status) : 255);
    if (journal("EXIT_OBSERVED")) return -1;
    char frame[256];
    snprintf(frame, sizeof(frame), "\"operation\":\"EXIT\",\"sequence\":%u,\"exit_code\":%d,\"pid\":%ld,\"start_ticks\":%llu",
        seq_out++, exit_code, (long)child_pid, child_ticks);
    return send_frame(frame);
}

static int send_stop_confirmed(void) {
    char frame[256];
    snprintf(frame, sizeof(frame), "\"operation\":\"STOP_CONFIRMED\",\"sequence\":%u,\"pid\":%ld,\"start_ticks\":%llu",
        seq_out++, (long)child_pid, child_ticks);
    return consume_marker("broker-stop-verified", p.stop, strlen(p.stop)) ||
           journal("STOP_VERIFIED") || send_frame(frame) ? -1 : 0;
}

static int receive_stop_if_ready(short revents) {
    if (revents & POLLIN) {
        if (receive_expected(p.stop)) return -1;
        stop_received = true;
        if (consume_marker("broker-stop-consumed", p.stop, strlen(p.stop)) ||
            journal("STOP_REQUESTED") || stop_child()) return -1;
        return 1;
    }
    return (revents & POLLHUP) ? -1 : 0;
}

static int wait_release_or_stop(unsigned long long deadline, int gate_write,
                               int workspace_fd, int file_fd, const struct stat *file_identity) {
    if (!strcmp(p.mode, "wait_for_stop")) {
        while (now_ms() < deadline) {
            struct pollfd req = {.fd=5,.events=POLLIN|POLLHUP};
            int remain = (int)(deadline - now_ms());
            int ready = poll(&req, 1, remain);
            if (ready < 0 && errno == EINTR) continue;
            if (ready <= 0) break;
            int stopped = receive_stop_if_ready(req.revents);
            if (stopped > 0) return send_exit() || send_stop_confirmed() ? -1 : 1;
            if (stopped < 0) return -1;
        }
        return -1;
    }
    for (;;) {
        struct stat st;
        int marker_fd = openat(journal_dir_fd, "broker-release", O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);
        if (marker_fd >= 0) {
            int ok = fstat(marker_fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_nlink == 1 &&
                     st.st_uid == geteuid() && (st.st_mode & 0777) == 0600;
            close(marker_fd);
            if (!ok) return -1;
            if (verify_head(p.head_sha) || verify_selected_file(workspace_fd, file_fd, file_identity)) return -1;
            const char release = 'R';
            return write_full(gate_write, &release, 1) ? -1 : 0;
        }
        if (errno != ENOENT || now_ms() >= deadline) return -1;
        struct pollfd req = {.fd=5,.events=POLLIN|POLLHUP};
        int ready = poll(&req, 1, 10);
        if (ready < 0 && errno != EINTR) return -1;
        if (ready > 0) {
            int stopped = receive_stop_if_ready(req.revents);
            if (stopped > 0) return send_exit() || send_stop_confirmed() ? -1 : 1;
            if (stopped < 0) return -1;
        }
    }
}

static int run_tool(void) {
    int workspace_fd = open(p.workspace, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    struct stat wst;
    char canonical[PATH_MAX];
    if (workspace_fd < 0 || fstat(workspace_fd, &wst) || !S_ISDIR(wst.st_mode) || wst.st_uid != geteuid() ||
        !realpath(p.workspace, canonical) || strcmp(canonical, p.workspace)) return -1;
    int file_fd = openat(workspace_fd, "planner_input.txt", O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    struct stat fst; char hash[65];
    if (file_fd < 0 || fstat(file_fd, &fst) || !S_ISREG(fst.st_mode) || fst.st_nlink < 1 ||
        digest_fd(file_fd, hash) || strcmp(hash, p.file_sha)) return -1;
    if (hash_path(p.shell_path, p.shell_sha) || trusted_ancestry(p.shell_path) || verify_head(p.head_sha)) return -1;
    unsigned long long now = now_ms();
    if (p.deadline <= now + STOP_RESERVE_MS) return -1;
    operation_deadline = now + TOOL_MS;
    if (operation_deadline > p.deadline - STOP_RESERVE_MS) operation_deadline = p.deadline - STOP_RESERVE_MS;
    if (operation_deadline <= now_ms() || consume_marker("broker-start-consumed", p.start, strlen(p.start)) ||
        journal("START_INTENT_DURABLE") || verify_selected_file(workspace_fd, file_fd, &fst)) return -1;
    int out[2], err[2], gate[2];
    if (pipe2(out, O_CLOEXEC | O_NONBLOCK) || pipe2(err, O_CLOEXEC | O_NONBLOCK) || pipe2(gate, O_CLOEXEC)) return -1;
    pid_t pid = fork();
    if (pid < 0) return -1;
    if (pid == 0) {
        if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != helper_pid) _exit(126);
        close(gate[1]);
        if (setpgid(0, 0) || fchdir(workspace_fd) || dup2(out[1], STDOUT_FILENO) < 0 || dup2(err[1], STDERR_FILENO) < 0) _exit(126);
        close(out[0]); close(out[1]); close(err[0]); close(err[1]); close(workspace_fd);
        close(3); close(4); close(5); close(6);
        char release;
        if (read_full(gate[0], &release, 1) || release != 'R') _exit(126);
        close(gate[0]);
        if (syscall(SYS_close_range, 3u, ~0u, 0u) != 0) _exit(126);
        if (install_tool_syscall_filter()) _exit(126);
        clearenv();
        char *const argv[] = {p.shell_path, "-c", "/usr/bin/head -n 8 -- planner_input.txt", NULL};
        char *const envp[] = {"PATH=/usr/bin:/bin", "LC_ALL=C", NULL};
        execve(p.shell_path, argv, envp);
        _exit(127);
    }
    child_pid = pid; child_group = pid;
    child_pidfd = (int)syscall(SYS_pidfd_open, pid, 0);
    close(gate[0]);
    close(out[1]); close(err[1]);
    setpgid(pid, pid);
    child_ticks = proc_start_ticks(pid);
    if (child_pidfd < 0 || !child_ticks || journal("STARTED")) return -1;
    char started[256];
    snprintf(started, sizeof(started), "\"operation\":\"STARTED\",\"sequence\":%u,\"pid\":%ld,\"start_ticks\":%llu",
        seq_out++, (long)child_pid, child_ticks);
    if (send_frame(started)) { close(gate[1]); return -1; }
    int release_result = wait_release_or_stop(operation_deadline, gate[1], workspace_fd, file_fd, &fst);
    close(gate[1]);
    close(file_fd); close(workspace_fd);
    if (release_result < 0) return -1;
    if (release_result > 0) { close(out[0]); close(err[0]); return 0; }
    unsigned long long total = 0;
    bool eof_out = false, eof_err = false, exited = false;
    unsigned char chunk[MAX_CHUNK];
    while ((!eof_out || !eof_err || !exited) && now_ms() < operation_deadline) {
        struct pollfd fds[3] = {{.fd=out[0],.events=POLLIN|POLLHUP},{.fd=err[0],.events=POLLIN|POLLHUP},
                                {.fd=5,.events=POLLIN|POLLHUP}};
        int ready = poll(fds, 3, 20);
        if (ready < 0 && errno != EINTR) goto fail;
        int stopped = receive_stop_if_ready(fds[2].revents);
        if (stopped < 0) goto fail;
        if (stopped > 0) exited = true;
        for (int i = 0; i < 2; i++) {
            if ((i == 0 && eof_out) || (i == 1 && eof_err)) continue;
            if (!(fds[i].revents & (POLLIN|POLLHUP))) continue;
            ssize_t n = read(fds[i].fd, chunk, sizeof(chunk));
            if (n > 0) {
                if (total == 0 && journal("OUTPUT_STREAMING")) goto fail;
                total += (unsigned long long)n;
                if (total > MAX_TOTAL || emit_output(i, chunk, (size_t)n)) goto fail;
            }
            else if (n == 0) { if (i == 0) eof_out=true; else eof_err=true; }
            else if (errno != EAGAIN && errno != EINTR) goto fail;
        }
        if (!stop_received) {
            int observed = observe_child_exit();
            if (observed < 0) goto fail;
            if (observed > 0) exited = true;
        }
    }
    if (!exited) goto fail;
    if (!stop_received && send_exit()) goto fail;
    if (stop_received && send_exit()) goto fail;
    if (stop_received && send_stop_confirmed()) goto fail;
    close(out[0]); close(err[0]);
    return 0;
fail:
    close(out[0]); close(err[0]);
    return -1;
}

int main(void) {
    clearenv();
    helper_pid = getpid();
    helper_ppid = getppid();
    helper_ticks = proc_start_ticks(getpid());
    if (syscall(SYS_close_range, 7u, ~0u, 0u) != 0) return 2;
    close(3);
    if (read_permit() || validate_channels()) return 2;
    int jdir = open(p.journal, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    struct stat st;
    char canonical[PATH_MAX];
    if (jdir < 0 || fstat(jdir, &st) || !S_ISDIR(st.st_mode) || st.st_uid != geteuid() ||
        (st.st_mode & 0777) != 0700 || !realpath(p.journal, canonical) || strcmp(canonical, p.journal)) return 2;
    journal_fd = openat(jdir, "broker-events.jsonl", O_WRONLY | O_APPEND | O_CREAT | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (journal_fd < 0 || fstat(journal_fd, &st) || !S_ISREG(st.st_mode) || st.st_nlink != 1 || st.st_uid != geteuid() || (st.st_mode & 0777) != 0600) return 2;
    journal_dir_fd = jdir;
    if (journal("PERMITTED")) return 2;
    if (receive_expected(p.start)) {
        send_frame("\"operation\":\"REFUSED\",\"sequence\":1,\"reason\":\"invalid_request\"");
        return 3;
    }
    if (run_tool()) {
        if (child_pid > 0 && stop_child() == 0) journal("CHILD_STOPPED_AFTER_FAILURE");
        journal("QUARANTINED");
        char refused[160];
        snprintf(refused, sizeof(refused), "\"operation\":\"REFUSED\",\"sequence\":%u,\"reason\":\"tool_uncertain\"", seq_out++);
        send_frame(refused);
        return 4;
    }
    if (!stop_received) {
        if (receive_expected(p.stop)) {
            journal("QUARANTINED");
            char refused[160];
            snprintf(refused, sizeof(refused), "\"operation\":\"REFUSED\",\"sequence\":%u,\"reason\":\"invalid_request\"", seq_out++);
            send_frame(refused);
            return 5;
        }
        if (consume_marker("broker-stop-consumed", p.stop, strlen(p.stop)) ||
            journal("STOP_REQUESTED") || stop_child() || send_stop_confirmed()) {
            journal("QUARANTINED"); return 6;
        }
    }
    while (now_ms() < p.deadline) {
        struct pollfd request = {.fd=5,.events=POLLIN|POLLHUP};
        unsigned long long remain = p.deadline - now_ms();
        int wait = remain > 1000 ? 1000 : (int)remain;
        int ready = poll(&request, 1, wait);
        if (ready < 0 && errno == EINTR) continue;
        if (ready < 0) { journal("QUARANTINED"); return 7; }
        if (!ready) continue;
        if (request.revents & POLLIN) { journal("QUARANTINED"); return 7; }
        if (request.revents & POLLHUP) return 0;
    }
    journal("QUARANTINED");
    return 8;
}
