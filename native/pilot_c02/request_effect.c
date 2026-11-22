#include "request_effect.h"

#define EFFECT_STATES 5
#define EFFECT_LINE_MAX 1024

static const char *const states[EFFECT_STATES] = {
    "PRE_SEND_INTENT", "POSSIBLE_SEND_ACK", "INVOCATION_PERMITTED",
    "OBSERVED_ACCEPTANCE", "TERMINAL_CONFIRMATION"
};

static int transfer_exact(int fd, unsigned char *buffer, size_t length, bool writing,
                          unsigned long long deadline) {
    size_t offset = 0;
    while (offset < length) {
        if (!wait_fd(fd, writing ? POLLOUT : POLLIN, deadline)) return -1;
        ssize_t n = writing ? write(fd, buffer + offset, length - offset) : read(fd, buffer + offset, length - offset);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        offset += (size_t)n;
    }
    return 0;
}

int request_effect_read_frame(int fd, unsigned char *payload, size_t capacity,
                              size_t *length, unsigned long long deadline) {
    unsigned char prefix[4];
    if (!payload || !length || capacity == 0 || transfer_exact(fd, prefix, sizeof(prefix), false, deadline)) return -1;
    uint32_t size = ((uint32_t)prefix[0] << 24) | ((uint32_t)prefix[1] << 16) |
                    ((uint32_t)prefix[2] << 8) | (uint32_t)prefix[3];
    if (!size || size > 8192 || size > capacity || transfer_exact(fd, payload, size, false, deadline)) return -1;
    *length = size;
    return 0;
}

int request_effect_write_frame(int fd, const unsigned char *payload, size_t length,
                               unsigned long long deadline) {
    if (!payload || !length || length > 8192) return -1;
    uint32_t size = (uint32_t)length;
    unsigned char prefix[4] = {(unsigned char)(size >> 24), (unsigned char)(size >> 16),
                               (unsigned char)(size >> 8), (unsigned char)size};
    if (transfer_exact(fd, prefix, sizeof(prefix), true, deadline)) return -1;
    return transfer_exact(fd, (unsigned char *)payload, length, true, deadline);
}

static int state_index(const char *state) {
    for (int i = 0; i < EFFECT_STATES; i++) if (!strcmp(states[i], state)) return i;
    return -1;
}

static bool safe_id(const char *value) {
    size_t n = strlen(value);
    if (!n || n > 64) return false;
    for (size_t i = 0; i < n; i++)
        if (!((value[i] >= 'a' && value[i] <= 'z') || (value[i] >= 'A' && value[i] <= 'Z') ||
              (value[i] >= '0' && value[i] <= '9') || value[i] == '_' || value[i] == '-')) return false;
    return true;
}

static int last_state(int fd, char *last, size_t capacity, const char *binding,
                      const char *attempt, const char *request_id,
                      const char *descriptor, unsigned ordinal, const char *nonce) {
    if (lseek(fd, 0, SEEK_SET) < 0) return -1;
    FILE *stream = fdopen(dup(fd), "r");
    if (!stream) return -1;
    char line[EFFECT_LINE_MAX];
    bool seen = false;
    while (fgets(line, sizeof(line), stream)) {
        char b[65], a[129], id[65], state[40], digest[65], n[65];
        unsigned long rev = 0;
        unsigned ord = 0;
        unsigned long long at = 0;
        int consumed = 0;
        if (sscanf(line, "{\"binding\":\"%64[0-9a-f]\",\"attempt\":\"%128[0-9A-Za-z_-]\",\"request_id\":\"%64[0-9A-Za-z_-]\",\"state\":\"%39[A-Z_]\",\"descriptor_sha256\":\"%64[0-9a-f]\",\"revision\":%lu,\"ordinal\":%u,\"nonce\":\"%64[0-9a-f]\",\"at_ms\":%llu}%n",
                   b, a, id, state, digest, &rev, &ord, n, &at, &consumed) != 9 ||
            line[consumed] != '\n' || line[consumed + 1] != 0 ||
            strcmp(b, binding) || strcmp(a, attempt) || strcmp(id, request_id) ||
            strcmp(digest, descriptor) || ord != ordinal || strcmp(n, nonce)) {
            fclose(stream);
            return -1;
        }
        int current_state = state_index(state);
        unsigned long expected_revision = current_state < 2 ? 1UL : current_state == 2 ? 2UL : current_state == 3 ? 2UL : 3UL;
        if (current_state < 0 || rev != expected_revision) { fclose(stream); return -1; }
        if (seen) {
            int before = state_index(last), after = state_index(state);
            if (before < 0 || after != before + 1) { fclose(stream); return -1; }
        } else if (strcmp(state, states[0])) { fclose(stream); return -1; }
        if (strlen(state) + 1 > capacity) { fclose(stream); return -1; }
        strcpy(last, state);
        seen = true;
    }
    bool failed = ferror(stream);
    fclose(stream);
    return failed ? -1 : (seen ? 0 : 1);
}

int request_effect_record(const char *root, const char *binding, const char *attempt,
                          const char *request_id, const char *state,
                          const char *descriptor_sha256, unsigned long revision,
                          unsigned ordinal, const char *nonce) {
    int next = state_index(state);
    if (next < 0 || !hex64(binding) || !reference(attempt) || !safe_id(request_id) ||
        !hex64(descriptor_sha256) || !hex64(nonce) || !revision || ordinal < 1 || ordinal > 2 ||
        (root_fd = open_root(root)) < 0 || read_permit() || strcmp(authority.binding, binding) ||
        strcmp(authority.attempt, attempt) || strcmp(authority.profile, SCHEMA2_PROFILE)) return -1;

    char filename[96];
    if (snprintf(filename, sizeof(filename), "request-effect-%s.jsonl", request_id) >= (int)sizeof(filename)) return -1;
    int fd = openat(root_fd, filename, O_RDWR | O_APPEND | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
    bool fresh = fd >= 0;
    if (!fresh && errno == EEXIST) fd = openat(root_fd, filename, O_RDWR | O_APPEND | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
    struct stat st;
    if (fd < 0 || fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_nlink != 1 ||
        st.st_uid != geteuid() || (st.st_mode & 0777) != 0600 || st.st_size >= 6144 || flock(fd, LOCK_EX)) {
        if (fd >= 0) close(fd);
        return -1;
    }
    char previous[40] = {0};
    int prior = fresh ? 1 : last_state(fd, previous, sizeof(previous), binding, attempt, request_id,
                                       descriptor_sha256, ordinal, nonce);
    unsigned long expected_revision = next < 2 ? 1UL : next < 4 ? 2UL : 3UL;
    bool allowed = revision == expected_revision &&
                   ((fresh && next == 0) || (!fresh && prior == 0 && state_index(previous) + 1 == next));
    char line[EFFECT_LINE_MAX];
    int size = snprintf(line, sizeof(line),
        "{\"binding\":\"%s\",\"attempt\":\"%s\",\"request_id\":\"%s\",\"state\":\"%s\",\"descriptor_sha256\":\"%s\",\"revision\":%lu,\"ordinal\":%u,\"nonce\":\"%s\",\"at_ms\":%llu}\n",
        binding, attempt, request_id, state, descriptor_sha256, revision, ordinal, nonce, monotonic_ms());
    bool ok = allowed && size > 0 && (size_t)size < sizeof(line) &&
              write(fd, line, (size_t)size) == size && !fsync(fd) && !fsync(root_fd);
    flock(fd, LOCK_UN);
    close(fd);
    if (!ok && fresh) unlinkat(root_fd, filename, 0);
    return ok ? 0 : -1;
}

int main(int argc, char **argv) {
    if (argc != 10) return 64;
    char *end = NULL;
    unsigned long revision = strtoul(argv[7], &end, 10);
    if (!end || *end || !revision) return 64;
    unsigned long ordinal = strtoul(argv[8], &end, 10);
    if (!end || *end || ordinal > UINT_MAX) return 64;
    return request_effect_record(argv[1], argv[2], argv[3], argv[4], argv[5], argv[6],
                                 revision, (unsigned)ordinal, argv[9]) ? 1 : 0;
}
