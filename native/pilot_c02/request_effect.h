#ifndef SYMPHONY_NATIVE_REQUEST_EFFECT_H
#define SYMPHONY_NATIVE_REQUEST_EFFECT_H

#include "common.h"

/* A subordinate, synchronized observation journal for one synthetic request. */
int request_effect_record(const char *root, const char *binding, const char *attempt,
                          const char *request_id, const char *state,
                          const char *descriptor_sha256, unsigned long revision,
                          unsigned ordinal, const char *nonce);
int request_effect_read_frame(int fd, unsigned char *payload, size_t capacity,
                              size_t *length, unsigned long long deadline);
int request_effect_write_frame(int fd, const unsigned char *payload, size_t length,
                               unsigned long long deadline);

#endif
