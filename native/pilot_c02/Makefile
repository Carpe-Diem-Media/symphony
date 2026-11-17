CC := /usr/bin/cc
CFLAGS := -std=c17 -O2 -g -Wall -Wextra -Werror -fstack-protector-strong -D_FORTIFY_SOURCE=3
LDFLAGS := -Wl,-z,relro,-z,now
BUILD := build
.PHONY: all check clean
all: $(BUILD)/host $(BUILD)/guard $(BUILD)/holder-probe
$(BUILD):
	mkdir -p $@
$(BUILD)/host: host.c common.h | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) host.c -o $@ -lcrypto
$(BUILD)/guard: guard.c common.h | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) guard.c -o $@ -lcrypto
$(BUILD)/holder-probe: holder_probe.c | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) holder_probe.c -o $@
check: all
	/usr/bin/python3 -I tests/test_native.py
clean:
	rm -f $(BUILD)/host $(BUILD)/guard $(BUILD)/holder-probe
