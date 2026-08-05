CC      = gcc
CFLAGS  = -fPIC -shared -Ibackend/include
TEST_CFLAGS = -Ibackend/include

ifeq ($(DEBUG),1)
CFLAGS += -DDEBUG -g
TEST_CFLAGS += -DDEBUG -g
endif

SRC_DIR = backend/src
C_TEST_DIR = backend/tests/c
PY_TEST_DIR = backend/tests/python
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

SRCS = $(wildcard $(SRC_DIR)/*.c)
C_TEST_SRCS = $(C_TEST_DIR)/test_trie.c $(SRC_DIR)/trie.c

TARGET = $(SRC_DIR)/libtrie.so
C_TEST_TARGET = $(C_TEST_DIR)/test_trie

# ── Default target ────────────────────────────────────────────────
all: $(TARGET)

# ── Test targets ────────────────────────────────────────────────────
test: test-c test-python

test-c: $(C_TEST_TARGET)
	./$(C_TEST_TARGET)

test-python: $(TARGET)
	$(PYTHON) -m unittest discover -s $(PY_TEST_DIR) -p 'test_*.py' -v

# ── Link ──────────────────────────────────────────────────────────
$(TARGET): $(SRCS)
	$(CC) $(CFLAGS) $^ -o $@

$(C_TEST_TARGET): $(C_TEST_SRCS)
	$(CC) $(TEST_CFLAGS) $^ -o $@

.PHONY: clean test test-c test-python

# ── Clean ─────────────────────────────────────────────────────────
clean:
	rm -f backend/src/libtrie.so $(C_TEST_TARGET)
