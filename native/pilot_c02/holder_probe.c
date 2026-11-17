/* Executable test of early holder restrictions. This is NOT patched Codex. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/ptrace.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>
#define DENY(n) BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (n), 0, 1), BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM)
static int protect(void) {
    struct rlimit core = {0, 0};
    struct sock_filter code[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000U, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        DENY(SYS_fork), DENY(SYS_vfork), DENY(SYS_clone), DENY(SYS_clone3), DENY(SYS_execve), DENY(SYS_execveat),
        DENY(SYS_ptrace), DENY(SYS_process_vm_readv), DENY(SYS_process_vm_writev), DENY(SYS_pidfd_getfd), DENY(SYS_kcmp),
        DENY(SYS_bpf), DENY(SYS_perf_event_open), DENY(SYS_unshare), DENY(SYS_setns), DENY(SYS_mount), DENY(SYS_socket),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)
    };
    struct sock_fprog program = {.len = sizeof(code) / sizeof(code[0]), .filter = code};
    return setrlimit(RLIMIT_CORE, &core) || prctl(PR_SET_DUMPABLE, 0) ||
        prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) || prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program);
}
int main(int argc, char **argv) {
    /* Synchronous entry: before inspecting material, config or starting threads. */
    if (protect()) return 92;
    if (argc != 3) return 93;
    const char *material = getenv("ACCESS_TOKEN");
    struct rlimit core;
    if (!material || strncmp(material, "SYNTHETIC-NONLIVE-", 18) || strlen(material) != 50 || getrlimit(RLIMIT_CORE, &core)) return 94;
    long child = syscall(SYS_fork);
    if (child == 0) _exit(95);
    int fork_denied = child < 0 && errno == EPERM;
    int exec_denied = syscall(SYS_execve, "/nonexistent-c02-probe", NULL, NULL) < 0 && errno == EPERM;
    int ptrace_denied = syscall(SYS_ptrace, PTRACE_PEEKDATA, getpid(), NULL, NULL) < 0 && errno == EPERM;
    int network_socket = socket(AF_INET, SOCK_STREAM, 0);
    int network_denied = network_socket < 0 && errno == EPERM;
    if (network_socket >= 0) close(network_socket);
    int fds_absent = 1;
    for (int fd = 3; fd < 1024; fd++) if (fcntl(fd, F_GETFD) >= 0 || errno != EBADF) fds_absent = 0;
    struct stat home, codex;
    const char *home_path = getenv("HOME"), *codex_path = getenv("CODEX_HOME");
    int fresh = home_path && codex_path && !stat(home_path, &home) && !stat(codex_path, &codex) &&
        S_ISDIR(home.st_mode) && S_ISDIR(codex.st_mode) && (home.st_mode & 0777) == 0700 && (codex.st_mode & 0777) == 0700;
    if (prctl(PR_GET_DUMPABLE) != 0 || prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0) != 1 ||
        core.rlim_cur != 0 || core.rlim_max != 0 || !fork_denied || !exec_denied || !ptrace_denied ||
        !network_denied || !fds_absent || !fresh) return 98;
    printf("{\"ready\":true,\"binding\":\"%s\",\"controls\":{\"nondumpable\":%s,\"no_new_privs\":%s,\"core_zero\":%s,"
        "\"fork_denied\":%s,\"exec_denied\":%s,\"ptrace_denied\":%s,\"inet_socket_denied\":%s,\"credential_fds_absent\":%s,\"fresh_home\":%s}}\n",
        argv[1], prctl(PR_GET_DUMPABLE) == 0 ? "true" : "false", prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0) == 1 ? "true" : "false",
        core.rlim_cur == 0 && core.rlim_max == 0 ? "true" : "false", fork_denied ? "true" : "false", exec_denied ? "true" : "false",
        ptrace_denied ? "true" : "false", network_denied ? "true" : "false", fds_absent ? "true" : "false", fresh ? "true" : "false");
    fflush(stdout);
    char line[16];
    if (!fgets(line, sizeof(line), stdin) || strcmp(line, "infer\n")) return 96;
    if (!strcmp(argv[2], "ambiguous_provider")) _exit(97);
    if (!strcmp(argv[2], "continuous")) { for (;;) { puts("NONSECRET_PROGRESS"); fflush(stdout); usleep(1000); } }
    puts("INFERENCE_REFUSED"); fflush(stdout);
    /* Never a model call: strict test holder has no inference implementation. */
    return 0;
}
