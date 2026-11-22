/* The resident guard never opens the materialization channel or receives material. */
#include "common.h"
extern char **environ;

static int sealed_holder(const char *path, const char *expected, bool pinned) {
    int input = open(path, O_RDONLY | O_NOFOLLOW | O_CLOEXEC | O_NONBLOCK);
    struct stat st;
    if (input < 0 || fstat(input, &st) || !S_ISREG(st.st_mode) || st.st_size < 4 || st.st_size > (pinned ? 1024LL * 1024 * 1024 : 16 * 1024 * 1024)) { if (input >= 0) close(input); return -1; }
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
static int sealed_manifest(const char *fault) {
    int fd = (int)syscall(SYS_memfd_create, "symphony-pinned-codex-manifest", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (fd < 0) return -1;
    char bytes[1024];
    const char *binding = !strcmp(fault, "manifest_wrong_binding") ? "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" : authority.binding;
    const char *holder = !strcmp(fault, "manifest_wrong_identity") ? "0000000000000000000000000000000000000000000000000000000000000000" : authority.holder;
    const char *selected_fault = (!strcmp(fault, "continuous") || !strcmp(fault, "ambiguous_provider") || !strcmp(fault, "controls_unavailable")) ? fault : "none";
    int size = snprintf(bytes, sizeof(bytes), "{\"schema\":1,\"profile\":\"C02_PINNED_CODEX_SYNTHETIC_V1\",\"binding\":\"%s\",\"attempt\":\"%s\",\"holder_sha256\":\"%s\",\"deadline_ms\":%llu,\"fault\":\"%s\"}",
        binding, authority.attempt, holder, authority.deadline, selected_fault);
    if (size < 1 || (size_t)size >= sizeof(bytes) || write(fd, bytes, (size_t)size) != size || lseek(fd, 0, SEEK_SET) < 0 ||
        (strcmp(fault, "manifest_unsealed") && fcntl(fd, F_ADD_SEALS, F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL))) {
        close(fd); return -1;
    }
    return fd;
}
/* Seal the exact nonsecret manifest identified by the synthetic permit. */
static int sealed_private_input(const char *name, const char *expected, size_t limit) {
    int fd = openat(root_fd, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
    struct stat st;
    if (fd < 0 || fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_nlink != 1 ||
        st.st_uid != geteuid() || (st.st_mode & 0777) != 0600 || st.st_size < 2 || (size_t)st.st_size > limit) {
        if (fd >= 0) close(fd);
        return -1;
    }
    int sealed = (int)syscall(SYS_memfd_create, "symphony-schema2-manifest", MFD_CLOEXEC | MFD_ALLOW_SEALING);
    if (sealed < 0) { close(fd); return -1; }
    char bytes[4096], digest[65];
    size_t total = 0;
    ssize_t n;
    while ((n = read(fd, bytes, sizeof(bytes))) > 0) {
        total += (size_t)n;
        if (total > limit || monotonic_ms() >= authority.deadline || write(sealed, bytes, (size_t)n) != n) break;
    }
    close(fd);
    if (n != 0 || total != (size_t)st.st_size ||
        fcntl(sealed, F_ADD_SEALS, F_SEAL_WRITE | F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_SEAL) ||
        digest_fd(sealed, digest) || strcmp(digest, expected) || lseek(sealed, 0, SEEK_SET) < 0) {
        close(sealed);
        return -1;
    }
    return sealed;
}

/* The Rust holder owns RPC admission. Forward only bounded pipe data until EOF
 * or the original execution deadline. The guard never receives material. */
static bool relay_schema2(int *input, int output, pid_t child, unsigned long long deadline,
                          bool *stop_requested) {
    size_t sent = 0, received = 0;
    char bytes[4096];
    for (;;) {
        unsigned long long now = monotonic_ms();
        if (now >= deadline) return false;
        struct pollfd fds[] = {{.fd = *input >= 0 ? 0 : -1, .events = POLLIN}, {.fd = output, .events = POLLIN}};
        int ready = poll(fds, 2, (int)(deadline - now));
        if (ready < 0 && errno == EINTR) continue;
        if (ready <= 0) return false;
        if (fds[0].revents & (POLLIN | POLLHUP)) {
            ssize_t size = read(0, bytes, sizeof(bytes));
            if (size == 0) {
                if (event("TERMINATION_REQUESTED", child)) return false;
                *stop_requested = true;
                close(*input);
                *input = -1;
            }
            else if (size < 0 || (sent += (size_t)size) > 262144 ||
                !wait_fd(*input, POLLOUT, deadline) || write(*input, bytes, (size_t)size) != size) return false;
        }
        if (fds[1].revents & (POLLIN | POLLHUP)) {
            ssize_t size = read(output, bytes, sizeof(bytes));
            if (size == 0) return *input == -1;
            if (size < 0 || (received += (size_t)size) > 32768 ||
                !wait_fd(1, POLLOUT, deadline) || write(1, bytes, (size_t)size) != size) return false;
        }
        if ((fds[0].revents | fds[1].revents) & (POLLERR | POLLNVAL)) return false;
    }
}

/* Move sources out of the target range before dup2 can overwrite them. */
static int assign_descriptors(const int *source, size_t count, int first) {
    int duplicates[7];
    if (count > sizeof(duplicates) / sizeof(duplicates[0])) return -1;
    for (size_t i = 0; i < count; ++i) {
        duplicates[i] = fcntl(source[i], F_DUPFD_CLOEXEC, 16);
        if (duplicates[i] < 0) return -1;
    }
    for (size_t i = 0; i < count; ++i)
        if (dup2(duplicates[i], first + (int)i) < 0 || (first + (int)i == 3 &&
            fcntl(3, F_SETFD, FD_CLOEXEC))) return -1;
    return syscall(SYS_close_range, first + (unsigned int)count, UINT_MAX, 0) ? -1 : 0;
}

static int assign_holder_descriptors(int input, int output, int image, int manifest,
                                     const int broker[4], const int provider[4]) {
    int source[9] = {input, output, 2, image, manifest, -1, -1, -1, -1};
    int duplicate[9];
    if (broker) { source[5] = broker[1]; source[6] = broker[2]; }
    if (provider) { source[7] = provider[1]; source[8] = provider[2]; }
    for (size_t i = 0; i < 9; i++) {
        duplicate[i] = source[i] >= 0 ? fcntl(source[i], F_DUPFD_CLOEXEC, 20) : -1;
        if (source[i] >= 0 && duplicate[i] < 0) return -1;
    }
    for (size_t i = 0; i < 9; i++) {
        if (duplicate[i] >= 0) {
            if (dup2(duplicate[i], (int)i) < 0 || (i == 3 && fcntl(3, F_SETFD, FD_CLOEXEC))) return -1;
        } else if (close((int)i) && errno != EBADF) return -1;
    }
    return syscall(SYS_close_range, 9U, UINT_MAX, 0) ? -1 : 0;
}

static bool broker_pipes(int fds[4], char **arguments) {
    struct stat identities[4];
    for (int i = 0; i < 4; ++i) {
        char *end = NULL;
        long fd = strtol(arguments[i], &end, 10);
        if (!end || *end || fd < 3 || fd > INT_MAX) return false;
        fds[i] = (int)fd;
        int flags = fcntl(fds[i], F_GETFL);
        if (flags < 0 || (flags & O_ACCMODE) != (i % 2 ? O_WRONLY : O_RDONLY) ||
            fstat(fds[i], &identities[i]) || !S_ISFIFO(identities[i].st_mode) ||
            fcntl(fds[i], F_SETFD, FD_CLOEXEC)) return false;
    }
    return identities[0].st_dev == identities[1].st_dev &&
           identities[0].st_ino == identities[1].st_ino &&
           identities[2].st_dev == identities[3].st_dev &&
           identities[2].st_ino == identities[3].st_ino &&
           (identities[0].st_dev != identities[2].st_dev ||
            identities[0].st_ino != identities[2].st_ino);
}

static bool provider_pipes(int fds[4], char **arguments) {
    struct stat identities[4];
    for (int i = 0; i < 4; ++i) {
        char *end = NULL;
        long fd = strtol(arguments[i], &end, 10);
        if (!end || *end || fd < 3 || fd > INT_MAX) return false;
        fds[i] = (int)fd;
        int flags = fcntl(fds[i], F_GETFL);
        int expected = (i % 2 == 0) ? O_RDONLY : O_WRONLY;
        if (flags < 0 || (flags & O_ACCMODE) != expected || fstat(fds[i], &identities[i]) ||
            !S_ISFIFO(identities[i].st_mode) || fcntl(fds[i], F_SETFD, FD_CLOEXEC)) return false;
    }
    return identities[0].st_dev == identities[1].st_dev && identities[0].st_ino == identities[1].st_ino &&
           identities[2].st_dev == identities[3].st_dev && identities[2].st_ino == identities[3].st_ino &&
           (identities[0].st_dev != identities[2].st_dev || identities[0].st_ino != identities[2].st_ino);
}

static int close_except_selected(const int *fds, size_t count) {
    unsigned int first = 3;
    for (;;) {
        unsigned int next = UINT_MAX;
        for (size_t i = 0; i < count; ++i)
            if ((unsigned int)fds[i] >= first && (unsigned int)fds[i] < next) next = (unsigned int)fds[i];
        if (first < next && syscall(SYS_close_range, first, next == UINT_MAX ? next : next - 1, 0))
            return -1;
        if (next == UINT_MAX) return 0;
        first = next + 1;
    }
}

static void start_broker(int image, int permit, const int pipes[4], pid_t parent) {
    /* The helper receives no inherited runtime environment or material channel. */
    if (prctl(PR_SET_PDEATHSIG, SIGTERM) || getppid() != parent) _exit(92);
    int null = open("/dev/null", O_RDWR | O_CLOEXEC);
    const int source[] = {null, null, null, image, permit, pipes[0], pipes[3]};
    if (null < 0 || assign_descriptors(source, 7, 0)) _exit(92);
    char *args[] = {"symphony-tool-broker", NULL};
    char *env[] = {NULL};
    syscall(SYS_execveat, 3, "", args, env, AT_EMPTY_PATH);
    _exit(92);
}

static void bootstrap(const char *root, const char *fault, int image, int manifest, int input, int output,
                      pid_t guard_pid, const int pipes[4], const int provider[4]) {
    if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != guard_pid) _exit(82);
    if (!strcmp(fault, "bootstrap_failure") || !strcmp(fault, "before_materialization")) _exit(83);
    bool pinned = manifest >= 0;
    if (pipes || provider) {
        if (assign_holder_descriptors(input, output, image, manifest, pipes, provider)) _exit(84);
    } else {
        if (dup2(input, 0) < 0 || dup2(output, 1) < 0 || dup3(image, 3, O_CLOEXEC) < 0) _exit(84);
        if (pinned && ((manifest == 4 ? fcntl(4, F_SETFD, 0) : dup3(manifest, 4, 0)) < 0)) _exit(84);
        if (syscall(SYS_close_range, pinned ? 5U : 4U, UINT_MAX, 0)) _exit(84);
    }
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
    char *probe_args[] = {"symphony-c02-holder-probe", authority.binding, (char *)fault, NULL};
    char *codex_args[] = {"codex-app-server", "--symphony-pilot-holder", authority.binding, authority.attempt, NULL};
    syscall(SYS_execveat, 3, "", pinned ? codex_args : probe_args, env, AT_EMPTY_PATH);
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
    bool pinned = argc >= 8 && !strcmp(argv[7], "--pinned-codex");
    bool external = pinned && argc == 16 && !strcmp(argv[8], "--external-broker");
    bool broker = pinned && argc >= 13 && argv[8][0] == '/';
    int provider_at = external ? 11 : broker ? 13 : 8;
    bool provider = pinned && argc == provider_at + 5 && !strcmp(argv[provider_at], "--provider");
    if (external && !provider) return 70;
    if ((argc != 7 && !pinned) || (pinned && !provider && !broker && argc != 8) ||
        (broker && !provider && argc != 13) || (provider && !external && !broker && argc != 13) ||
        (provider && broker && argc != 18)) return 70;
    int broker_fds[4] = {-1, -1, -1, -1};
    if (broker && (!pinned || argv[8][0] != '/' || !broker_pipes(broker_fds, argv + 9))) return 70;
    if (external) {
        struct stat pipe_stat[2];
        for (int i = 0; i < 2; ++i) {
            char *end;
            long fd = strtol(argv[9 + i], &end, 10);
            if (*end || fd < 3 || fd > INT_MAX) return 70;
            int flags = fcntl((int)fd, F_GETFL);
            if (flags < 0 || (flags & O_ACCMODE) != (i ? O_RDONLY : O_WRONLY) ||
                fstat((int)fd, &pipe_stat[i]) || !S_ISFIFO(pipe_stat[i].st_mode)) return 70;
            broker_fds[1 + i] = (int)fd;
        }
        if (pipe_stat[0].st_dev == pipe_stat[1].st_dev && pipe_stat[0].st_ino == pipe_stat[1].st_ino) return 70;
    }
    int provider_fds[4] = {-1, -1, -1, -1};
    if (provider && !provider_pipes(provider_fds, argv + provider_at + 1)) return 70;
    if (external) for (int i = 1; i <= 2; i++) {
        struct stat broker_pipe;
        if (fstat(broker_fds[i], &broker_pipe)) return 70;
        for (int j = 0; j < 4; j++) {
            struct stat provider_pipe;
            if (fstat(provider_fds[j], &provider_pipe) ||
                (broker_pipe.st_dev == provider_pipe.st_dev && broker_pipe.st_ino == provider_pipe.st_ino)) return 70;
        }
    }
    const char *root = argv[1], *fault = argv[6];
    if (!hex64(argv[4]) || !reference(argv[5])) return 70;
    strcpy(authority.binding, argv[4]); strcpy(authority.attempt, argv[5]);
    pid_t parent = getppid();
    int inherited[8], inherited_count = 0;
    if (broker) for (int i = 0; i < 4; i++) inherited[inherited_count++] = broker_fds[i];
    if (external) for (int i = 1; i <= 2; i++) inherited[inherited_count++] = broker_fds[i];
    if (provider) for (int i = 0; i < 4; i++) inherited[inherited_count++] = provider_fds[i];
    if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != parent ||
        close_except_selected(inherited, (size_t)inherited_count)) return 71;
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
    int image = sealed_holder(argv[2], argv[3], pinned);
    if (image < 0 || strcmp(argv[3], authority.holder)) { event("HOLDER_IDENTITY_REFUSED", 0); return 0; }
    bool schema2 = !strcmp(authority.profile, SCHEMA2_PROFILE);
    if ((schema2 && !pinned) || (broker || external) != (authority.broker[0] != '\0') || ((broker || external) && !schema2) ||
        (external && !authority.provider_nonce[0]) ||
        (provider && !schema2)) {
        close(image); return 73;
    }
    int manifest = schema2 ? sealed_private_input("manifest.json", authority.manifest, 131072) :
                             (pinned ? sealed_manifest(fault) : -1);
    if (pinned && manifest < 0) { close(image); event("MANIFEST_REFUSED", 0); return 0; }
    int input[2], output[2];
    if (pipe2(input, O_CLOEXEC) || pipe2(output, O_CLOEXEC)) return 74;
    pid_t guard_pid = getpid();
    pid_t helper = -1;
    if (broker) {
        int helper_image = sealed_holder(argv[8], authority.broker, false);
        int permit = sealed_private_input("broker-permit", authority.broker_permit, 32768);
        if (helper_image < 0 || permit < 0) return 74;
        helper = fork();
        if (helper == 0) start_broker(helper_image, permit, broker_fds, guard_pid);
        close(helper_image); close(permit);
        close(broker_fds[0]); close(broker_fds[3]);
        if (helper < 0 || event("BROKER_CREATED", helper)) return 74;
    }
    pid_t child = fork();
    if (child == 0) bootstrap(root, fault, image, manifest, input[0], output[1], guard_pid,
                              (broker || external) ? broker_fds : NULL, provider ? provider_fds : NULL);
    close(image); if (manifest >= 0) close(manifest); close(input[0]); close(output[1]);
    if (broker || external) { close(broker_fds[1]); close(broker_fds[2]); }
    if (provider) for (int i = 0; i < 4; i++) close(provider_fds[i]);
    if (child < 0) { event("QUARANTINED", 0); return 0; }
    bool clean_shutdown = false;
    bool stop_requested = false;
    if (event("BOOTSTRAP_CREATED", child)) goto stopping;

    unsigned long long execution_deadline = authority.deadline > 200 ? authority.deadline - 200 : authority.deadline;
    char line[4096];
    if (schema2) {
        while (faccessat(root_fd, "channel-closed", F_OK, 0) && monotonic_ms() < execution_deadline) usleep(1000);
        if (faccessat(root_fd, "channel-closed", F_OK, 0) == 0 &&
            !event("SCHEMA2_CHANNEL_CLOSED_BEFORE_RPC", child))
            clean_shutdown = relay_schema2(&input[1], output[0], child, execution_deadline, &stop_requested);
        goto stopping;
    }
    bool ready = read_line(output[0], line, sizeof(line), execution_deadline) == 0;
    if (ready && !strncmp(line, "{\"ready\":true,", 14)) {
        while (faccessat(root_fd, "channel-closed", F_OK, 0) && monotonic_ms() < execution_deadline) usleep(1000);
        if (faccessat(root_fd, "channel-closed", F_OK, 0) == 0 && !event("HOLDER_READY", child)) {
            puts(line); fflush(stdout);
            if (!strcmp(fault, "launcher_loss") || !strcmp(fault, "parent_loss")) {
                while (monotonic_ms() < execution_deadline) usleep(1000);
            } else {
                const char *request = "infer\n";
                if (pinned) {
                    const char *initialize = "{\"id\":1,\"method\":\"initialize\",\"params\":{\"clientInfo\":{\"name\":\"symphony-native-test\",\"version\":\"1\"}}}\n";
                    if (write(input[1], initialize, strlen(initialize)) != (ssize_t)strlen(initialize) ||
                        read_line(output[0], line, sizeof(line), execution_deadline) || strncmp(line, "{\"id\":1,\"result\":", 17) ||
                        event("CODEX_INITIALIZED_NOT_AUTHENTICATED", child)) goto stopping;
                    request = "{\"id\":2,\"method\":\"thread/start\",\"params\":{}}\n";
                }
                if (event("INFERENCE_INTENT", child) || write(input[1], request, strlen(request)) != (ssize_t)strlen(request)) goto stopping;
                int response;
                do { response = read_line(output[0], line, sizeof(line), execution_deadline); }
                while (response == 0 && (!strcmp(line, "NONSECRET_PROGRESS") || (pinned && !strcmp(line, "{\"method\":\"symphony/progress\"}"))));
                if (!response && (!strcmp(line, "INFERENCE_REFUSED") || (pinned && !strcmp(line, "{\"error\":{\"code\":-32091,\"message\":\"SYMPHONY_HOST_UNQUALIFIED\"},\"id\":2}")))) {
                    if (!event("INFERENCE_REFUSED", child)) marker("controlled-refusal");
                } else event("INFERENCE_AMBIGUOUS", child);
            }
        }
    }
stopping:
    if (!stop_requested) event("TERMINATION_REQUESTED", child);
    if (input[1] >= 0) close(input[1]);
    close(output[0]);
    /* Kill only the exact direct child. PID reuse is impossible before waitpid. */
    if (!clean_shutdown) kill(child, SIGKILL);
    int status = 0;
    while (monotonic_ms() < authority.deadline) {
        pid_t r = waitpid(child, &status, WNOHANG);
        if (r == child) {
            if (schema2 && clean_shutdown && WIFEXITED(status) && WEXITSTATUS(status) == 0 &&
                !event("SCHEMA2_CLEAN_EXIT", child)) marker("schema2-clean-exit");
            if (!event("GUARD_REAPED", child)) marker("guard-reaped");
            break;
        }
        if (r < 0 && errno != EINTR) break;
        usleep(1000);
    }
    if (helper > 0) {
        int helper_status;
        bool reaped = false;
        while (monotonic_ms() < authority.deadline) {
            pid_t result = waitpid(helper, &helper_status, WNOHANG);
            if (result == helper) {
                reaped = WIFEXITED(helper_status) && WEXITSTATUS(helper_status) == 0 &&
                         !event("BROKER_REAPED", helper);
                break;
            }
            if (result < 0 && errno != EINTR) break;
            usleep(1000);
        }
        if (!reaped) event("QUARANTINED", helper);
    }
    if (faccessat(root_fd, "guard-reaped", F_OK, 0)) event("QUARANTINED", child);
    return 0;
}
