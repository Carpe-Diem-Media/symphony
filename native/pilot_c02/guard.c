/* The resident guard never opens the materialization channel or receives material. */
#include "common.h"
extern char **environ;

static int sealed_holder(const char *path, const char *expected) {
    int input = open(path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
    struct stat st;
    if (input < 0 || fstat(input, &st) || !S_ISREG(st.st_mode) || st.st_size < 4 || st.st_size > 16 * 1024 * 1024) { if (input >= 0) close(input); return -1; }
    int sealed = (int)syscall(SYS_memfd_create, "symphony-c02-holder-probe", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (sealed < 0) { close(input); return -1; }
    char buf[8192]; ssize_t n;
    while ((n = read(input, buf, sizeof(buf))) > 0) if (write(sealed, buf, (size_t)n) != n) { close(input); close(sealed); return -1; }
    close(input);
    char digest[65], magic[4];
    if (n < 0 || digest_fd(sealed, digest) || strcmp(digest, expected) || pread(sealed, magic, 4, 0) != 4 ||
        memcmp(magic, "\177ELF", 4) || fchmod(sealed, 0500) || fcntl(sealed, F_ADD_SEALS,
        F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL)) { close(sealed); return -1; }
    return sealed;
}
static void bootstrap(const char *root, const char *fault, int image, int input, int output, pid_t guard_pid) {
    if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != guard_pid) _exit(82);
    if (!strcmp(fault, "bootstrap_failure") || !strcmp(fault, "before_materialization")) _exit(83);
    if (dup2(input, 0) < 0 || dup2(output, 1) < 0 || dup3(image, 3, O_CLOEXEC) < 0 || syscall(SYS_close_range, 4U, UINT_MAX, 0)) _exit(84);
    struct sockaddr_un address;
    int channel = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    struct request request;
    memset(&request, 0, sizeof(request));
    strcpy(request.binding, authority.binding); strcpy(request.attempt, authority.attempt); strcpy(request.holder, authority.holder);
    if (!strcmp(fault, "wrong_attempt")) strcpy(request.attempt, "wrong-runtime-attempt");
    if (!strcmp(fault, "wrong_holder")) memset(request.holder, '0', 64);
    if (channel < 0 || endpoint(root, &address) || connect(channel, (struct sockaddr *)&address, sizeof(address))) _exit(85);
    ssize_t sent;
    if (!strcmp(fault, "ancillary_fd")) {
        char control[CMSG_SPACE(sizeof(int))] = {0};
        struct iovec io = {.iov_base = &request, .iov_len = sizeof(request)};
        struct msghdr message = {.msg_iov = &io, .msg_iovlen = 1, .msg_control = control, .msg_controllen = sizeof(control)};
        struct cmsghdr *header = CMSG_FIRSTHDR(&message);
        header->cmsg_level = SOL_SOCKET; header->cmsg_type = SCM_RIGHTS; header->cmsg_len = CMSG_LEN(sizeof(int));
        int transferred = 3;
        memcpy(CMSG_DATA(header), &transferred, sizeof(transferred));
        sent = sendmsg(channel, &message, MSG_NOSIGNAL);
    } else sent = send(channel, &request, sizeof(request), MSG_NOSIGNAL);
    if (sent != sizeof(request) || !wait_fd(channel, POLLIN, authority.deadline)) _exit(85);
    char ack = 0;
    if (receive_plain(channel, &ack, 1) != 1 || ack != 'V') _exit(86);
    struct rlimit core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core) || prctl(PR_SET_DUMPABLE, 0) || prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) ||
        send(channel, "P", 1, MSG_NOSIGNAL) != 1 || !wait_fd(channel, POLLIN, authority.deadline)) _exit(87);
    char access[96] = "ACCESS_TOKEN=";
    ssize_t received = receive_plain(channel, access + 13, sizeof(access) - 13);
    close(channel);
    if (received != 51 || memcmp(access + 13, "SYNTHETIC-NONLIVE-", 18) || access[63] != 0) { explicit_bzero(access, sizeof(access)); _exit(88); }
    if (!strcmp(fault, "after_materialization")) { explicit_bzero(access, sizeof(access)); _exit(89); }
    char home[PATH_MAX + 5], codex[PATH_MAX + 12];
    if (snprintf(home, sizeof(home), "HOME=%s/home", root) >= (int)sizeof(home) ||
        snprintf(codex, sizeof(codex), "CODEX_HOME=%s/codex-home", root) >= (int)sizeof(codex)) _exit(90);
    char *env[] = {home, codex, "LANG=C.UTF-8", access, NULL};
    char *args[] = {"symphony-c02-holder-probe", authority.binding, (char *)fault, NULL};
    syscall(SYS_execveat, 3, "", args, env, AT_EMPTY_PATH);
    explicit_bzero(access, sizeof(access)); _exit(91);
}
static int read_line(int fd, char *line, size_t capacity, unsigned long long deadline) {
    size_t used = 0;
    while (used + 1 < capacity && wait_fd(fd, POLLIN, deadline)) {
        char c;
        if (read(fd, &c, 1) != 1) return -1;
        if (c == '\n') { line[used] = 0; return 0; }
        line[used++] = c;
    }
    return -1;
}
int main(int argc, char **argv) {
    if (argc != 7) return 70;
    const char *root = argv[1], *fault = argv[6];
    if (!hex64(argv[4]) || !reference(argv[5])) return 70;
    strcpy(authority.binding, argv[4]); strcpy(authority.attempt, argv[5]);
    pid_t parent = getppid();
    if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != parent || syscall(SYS_close_range, 3U, UINT_MAX, 0)) return 71;
    if ((root_fd = open_root(root)) < 0) return 72;
    signal(SIGPIPE, SIG_IGN);
    puts("WAITING_PERMISSION"); fflush(stdout);
    char command[16];
    if (read_line(0, command, sizeof(command), monotonic_ms() + 3000) || strcmp(command, "GO") || read_permit() || strcmp(authority.binding, argv[4]) || strcmp(authority.attempt, argv[5])) { event("HOST_PERMISSION_REFUSED", 0); return 0; }
    pid_t ignored = 0; unsigned long long start = 0;
    char self_digest[65];
    if (proc_identity(getpid(), &ignored, &start) || getpid() != authority.guard_pid || start != authority.guard_start ||
        digest_path("/proc/self/exe", self_digest) || strcmp(self_digest, authority.guard) ||
        event("HOST_PERMISSION_VALIDATED", getpid())) return 73;
    int image = sealed_holder(argv[2], argv[3]);
    if (image < 0 || strcmp(argv[3], authority.holder)) { event("HOLDER_IDENTITY_REFUSED", 0); return 0; }
    int input[2], output[2];
    if (pipe2(input, O_CLOEXEC) || pipe2(output, O_CLOEXEC)) return 74;
    pid_t guard_pid = getpid();
    pid_t child = fork();
    if (child == 0) bootstrap(root, fault, image, input[0], output[1], guard_pid);
    close(image); close(input[0]); close(output[1]);
    if (child < 0) { event("QUARANTINED", 0); return 0; }
    if (event("BOOTSTRAP_CREATED", child)) goto stopping;

    unsigned long long execution_deadline = authority.deadline > 200 ? authority.deadline - 200 : authority.deadline;
    char line[2048];
    bool ready = read_line(output[0], line, sizeof(line), execution_deadline) == 0;
    if (ready && !strncmp(line, "{\"ready\":true,", 14)) {
        while (faccessat(root_fd, "channel-closed", F_OK, 0) && monotonic_ms() < execution_deadline) usleep(1000);
        if (faccessat(root_fd, "channel-closed", F_OK, 0) == 0 && !event("HOLDER_READY", child)) {
            puts(line); fflush(stdout);
            if (!strcmp(fault, "launcher_loss") || !strcmp(fault, "parent_loss")) {
                while (monotonic_ms() < execution_deadline) usleep(1000);
            } else if (!event("INFERENCE_INTENT", child) && write(input[1], "infer\n", 6) == 6) {
                int response;
                do { response = read_line(output[0], line, sizeof(line), execution_deadline); }
                while (response == 0 && !strcmp(line, "NONSECRET_PROGRESS"));
                if (!response && !strcmp(line, "INFERENCE_REFUSED")) {
                    if (!event("INFERENCE_REFUSED", child)) marker("controlled-refusal");
                } else event("INFERENCE_AMBIGUOUS", child);
            }
        }
    }
stopping:
    event("TERMINATION_REQUESTED", child);
    close(input[1]); close(output[0]);
    /* Kill only the exact direct child. PID reuse is impossible before waitpid. */
    kill(child, SIGKILL);
    int status = 0;
    while (monotonic_ms() < authority.deadline) {
        pid_t r = waitpid(child, &status, WNOHANG);
        if (r == child) { if (!event("GUARD_REAPED", child)) marker("guard-reaped"); break; }
        if (r < 0 && errno != EINTR) break;
        usleep(1000);
    }
    if (faccessat(root_fd, "guard-reaped", F_OK, 0)) event("QUARANTINED", child);
    return 0;
}
