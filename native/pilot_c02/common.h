#ifndef SYMPHONY_NATIVE_C02_COMMON_H
#define SYMPHONY_NATIVE_C02_COMMON_H
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <openssl/evp.h>
#include <poll.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* Synthetic native development profile only. No operational credential input. */
#define PROFILE "C02_SYNTHETIC_NATIVE_V1"
#define SCHEMA2_PROFILE "C02_SYNTHETIC_SCHEMA2_V1"
struct permit {
    char profile[40], binding[65], attempt[129], holder[65], guard[65];
    char manifest[65];
    int guard_pid;
    unsigned long long guard_start, deadline;
};
struct request { char binding[65], attempt[129], holder[65]; };
static int root_fd = -1;
static struct permit authority;
static inline unsigned long long monotonic_ms(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) _exit(90);
    return (unsigned long long)t.tv_sec * 1000 + (unsigned long long)t.tv_nsec / 1000000;
}
static inline bool hex64(const char *s) {
    if (strlen(s) != 64) return false;
    for (size_t i = 0; i < 64; i++) if (!((s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'f'))) return false;
    return true;
}
static inline bool reference(const char *s) {
    size_t n = strlen(s);
    if (n == 0 || n > 128) return false;
    for (size_t i = 0; i < n; i++) if (!((s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z') ||
        (s[i] >= '0' && s[i] <= '9') || s[i] == '_' || s[i] == '-')) return false;
    return true;
}
static inline int open_root(const char *path) {
    int fd = open(path, O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    struct stat st;
    if (fd < 0 || fstat(fd, &st) || st.st_uid != geteuid() || (st.st_mode & 0777) != 0700) { if (fd >= 0) close(fd); return -1; }
    if (fchdir(fd)) { close(fd); return -1; }
    return fd;
}
static inline int read_permit(void) {
    int fd = openat(root_fd, "permission", O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
    struct stat st;
    if (fd < 0) return -1;
    if (fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_nlink != 1 || st.st_uid != geteuid() ||
        (st.st_mode & 0777) != 0600 || st.st_size > 1024) { close(fd); return -1; }
    FILE *f = fdopen(fd, "r");
    if (!f) { close(fd); return -1; }
    struct permit candidate = {0};
    int n = fscanf(f, "%39s\n%64s\n%128s\n%64s\n%64s\n%d\n%llu\n%llu\n", candidate.profile,
        candidate.binding, candidate.attempt, candidate.holder, candidate.guard, &candidate.guard_pid,
        &candidate.guard_start, &candidate.deadline);
    bool schema2 = !strcmp(candidate.profile, SCHEMA2_PROFILE);
    if (schema2 && fscanf(f, "%64s\n", candidate.manifest) != 1) n = -1;
    int trailing = fgetc(f);
    fclose(f);
    if (n != 8 || trailing != EOF || (!schema2 && strcmp(candidate.profile, PROFILE)) ||
        (schema2 && !hex64(candidate.manifest)) || !hex64(candidate.binding) ||
        !hex64(candidate.holder) || !hex64(candidate.guard) || !reference(candidate.attempt) ||
        candidate.guard_pid < 2 || candidate.deadline <= monotonic_ms()) return -1;
    authority = candidate;
    return 0;
}
static inline int event(const char *state, int pid) {
    int fd = openat(root_fd, "events.jsonl", O_WRONLY | O_APPEND | O_CREAT | O_NOFOLLOW | O_CLOEXEC, 0600);
    struct stat st;
    if (fd < 0 || fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_nlink != 1 || st.st_uid != geteuid()) { if (fd >= 0) close(fd); return -1; }
    char line[512];
    int n = snprintf(line, sizeof(line), "{\"state\":\"%s\",\"binding\":\"%s\",\"attempt\":\"%s\",\"pid\":%d,\"at_ms\":%llu}\n",
        state, authority.binding, authority.attempt, pid, monotonic_ms());
    int result = -1;
    if (n > 0 && (size_t)n < sizeof(line) && !flock(fd, LOCK_EX) && write(fd, line, (size_t)n) == n && !fsync(fd)) result = 0;
    close(fd);
    return result;
}
static inline int marker(const char *name) {
    int fd = openat(root_fd, name, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) return -1;
    int r = write(fd, authority.binding, 64) == 64 && !fsync(fd) && !fsync(root_fd) ? 0 : -1;
    close(fd);
    return r;
}
static inline int digest_fd(int fd, char out[65]) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    unsigned char hash[32], buf[8192];
    unsigned int length = 0;
    if (!ctx || lseek(fd, 0, SEEK_SET) < 0 || EVP_DigestInit_ex(ctx, EVP_sha256(), NULL) != 1) { EVP_MD_CTX_free(ctx); return -1; }
    ssize_t n;
    while ((n = read(fd, buf, sizeof(buf))) > 0) if (EVP_DigestUpdate(ctx, buf, (size_t)n) != 1) { EVP_MD_CTX_free(ctx); return -1; }
    int ok = n == 0 && EVP_DigestFinal_ex(ctx, hash, &length) == 1 && length == 32;
    EVP_MD_CTX_free(ctx);
    if (!ok) return -1;
    for (size_t i = 0; i < 32; i++) snprintf(out + i * 2, 3, "%02x", hash[i]);
    return 0;
}
static inline int digest_path(const char *path, char out[65]) {
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    int r = digest_fd(fd, out); close(fd); return r;
}
static inline int proc_identity(pid_t pid, pid_t *parent, unsigned long long *start) {
    char path[64], buf[4096];
    snprintf(path, sizeof(path), "/proc/%d/stat", pid);
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return -1;
    ssize_t n = read(fd, buf, sizeof(buf) - 1); close(fd);
    if (n < 1) return -1;
    buf[n] = 0;
    char *end = strrchr(buf, ')');
    if (!end || end[1] != ' ') return -1;
    char *save = NULL, *part = strtok_r(end + 2, " ", &save);
    for (int field = 3; part; field++, part = strtok_r(NULL, " ", &save)) {
        if (field == 4) *parent = (pid_t)strtol(part, NULL, 10);
        if (field == 22) { *start = strtoull(part, NULL, 10); return *start ? 0 : -1; }
    }
    return -1;
}
static inline int wait_fd(int fd, short flags, unsigned long long deadline) {
    unsigned long long now = monotonic_ms();
    if (now >= deadline) return 0;
    struct pollfd p = {.fd = fd, .events = flags};
    int r;
    do { r = poll(&p, 1, (int)(deadline - now)); } while (r < 0 && errno == EINTR && monotonic_ms() < deadline);
    return r > 0 && (p.revents & flags) ? 1 : 0;
}
/* Ancillary descriptors are always closed and refused, including truncation. */
static inline ssize_t receive_plain(int fd, void *bytes, size_t size) {
    char control[CMSG_SPACE(sizeof(int) * 16)];
    struct iovec io = {.iov_base = bytes, .iov_len = size};
    struct msghdr msg = {.msg_iov = &io, .msg_iovlen = 1, .msg_control = control, .msg_controllen = sizeof(control)};
    ssize_t n = recvmsg(fd, &msg, MSG_CMSG_CLOEXEC);
    bool ancillary = false;
    for (struct cmsghdr *c = CMSG_FIRSTHDR(&msg); c; c = CMSG_NXTHDR(&msg, c)) {
        ancillary = true;
        if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_RIGHTS && c->cmsg_len >= CMSG_LEN(0)) {
            size_t count = (c->cmsg_len - CMSG_LEN(0)) / sizeof(int);
            int *fds = (int *)CMSG_DATA(c);
            for (size_t i = 0; i < count; i++) close(fds[i]);
        }
    }
    return ancillary || (msg.msg_flags & (MSG_CTRUNC | MSG_TRUNC)) ? -1 : n;
}
static inline int endpoint(const char *root, struct sockaddr_un *address) {
    memset(address, 0, sizeof(*address)); address->sun_family = AF_UNIX;
    /* Both peers fchdir into the verified private evidence directory. */
    if (!root || root[0] != '/') return -1;
    strcpy(address->sun_path, "materialize.sock");
    return 0;
}
#endif
