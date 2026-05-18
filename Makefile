# ──────────────────────────────────────────────────────────────────────────────
# paperjson — Build for every installed Python version
#
# Phony targets (all list test clean help) do what they say.
# Any *other* target name is treated as a Python executable and passed
# directly to ``uv build --python <that>``.
#
# Examples
# --------
#   make                    Build for every detected CPython version
#   make test               Run pytest across all detected Python versions
#   make 3.10               Build with ``uv build --python 3.10``
#   make python3.12         Build with ``uv build --python python3.12``
#   make /usr/bin/python3   Build with that interpreter
#   make list               Show detected CPython versions
#   make clean              Remove dist/
# ──────────────────────────────────────────────────────────────────────────────

# Installed CPython versions, e.g. "3.10 3.11 3.12 3.14"
PYTHON_VERSIONS := $(shell uv python list --only-installed \
	| sed -n 's/^cpython-\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' \
	| sort -u)

DIST_DIR ?= dist

# ── Phony targets ────────────────────────────────────────────────────────────

.PHONY: all list test clean help

all:
	@for v in $(PYTHON_VERSIONS); do \
		echo "Building for Python $$v"; \
		uv build --python "$$v" --out-dir "$(DIST_DIR)"; \
	done
	@echo "All builds complete."

test:
	@failed=; \
	for v in $(PYTHON_VERSIONS); do \
		echo "=== pytest on Python $$v ==="; \
		if uv run --python "$$v" --frozen pytest -q --tb=short \
			2>&1 | tail -5; then \
			echo "Python $$v: PASSED"; \
		else \
			echo "Python $$v: FAILED"; \
			failed="$$failed $$v"; \
		fi; \
	done; \
	if [ -n "$$failed" ]; then \
		echo "FAILED versions:$$failed"; \
		exit 1; \
	fi

list:
	@echo "Installed Python versions (major.minor):"
	@for v in $(PYTHON_VERSIONS); do echo "  $$v"; done

clean:
	rm -rf $(DIST_DIR)

help:
	@echo "Usage:"
	@echo "  make              Build for all detected Python versions"
	@echo "  make test         Run pytest across all detected Python versions"
	@echo "  make <exe>        Build with that Python executable (e.g. 3.10, python3.12)"
	@echo "  make list         List detected Python versions"
	@echo "  make clean        Remove $(DIST_DIR)/"
	@echo ""
	@echo "Detected versions: $(PYTHON_VERSIONS)"

# ── Catch-all ────────────────────────────────────────────────────────────────
# Anything that isn't a phony target is treated as a Python executable name
# and passed straight to ``uv build --python``.

%:
	uv build --python "$@" --out-dir "$(DIST_DIR)"
