CC := /usr/bin/cc
CFLAGS := -std=c17 -O2 -g -Wall -Wextra -Werror -fstack-protector-strong -D_FORTIFY_SOURCE=3
LDFLAGS := -Wl,-z,relro,-z,now
BUILD := build
.PHONY: all check clean
all: $(BUILD)/host $(BUILD)/guard $(BUILD)/holder-probe $(BUILD)/tool-broker $(BUILD)/request-effect
$(BUILD):
	mkdir -p $@
$(BUILD)/host: host.c common.h | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) host.c -o $@ -lcrypto
$(BUILD)/guard: guard.c common.h | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) guard.c -o $@ -lcrypto
$(BUILD)/holder-probe: holder_probe.c | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) holder_probe.c -o $@
$(BUILD)/tool-broker: tool_broker.c | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) tool_broker.c -o $@ -lcrypto
$(BUILD)/request-effect: request_effect.c request_effect.h common.h | $(BUILD)
	$(CC) $(CFLAGS) $(LDFLAGS) request_effect.c -o $@ -lcrypto
check: all
	/usr/bin/python3 -I tests/test_native.py
	/usr/bin/python3 -I tests/test_tool_broker.py
	/usr/bin/python3 -I tests/test_provider_effects.py
clean:
	rm -f $(BUILD)/host $(BUILD)/guard $(BUILD)/holder-probe $(BUILD)/tool-broker $(BUILD)/request-effect
