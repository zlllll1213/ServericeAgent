.PHONY: dev test eval lint format coverage docker-up docker-down seed

PYTHON ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

dev:
	$(PYTHON) app/seed.py
	$(PYTHON) -m uvicorn main:app --reload --host 127.0.0.1 --port 8001

test:
	$(PYTHON) -m pytest -q

eval:
	$(PYTHON) evals/run_eval.py --all

lint:
	@if $(PYTHON) -c "import importlib.util; raise SystemExit(importlib.util.find_spec('ruff') is None)"; then \
		$(PYTHON) -m ruff check .; \
	else \
		echo "ruff not installed; running compileall fallback"; \
		$(PYTHON) -m compileall app main.py evals scripts; \
	fi

format:
	@if $(PYTHON) -c "import importlib.util; raise SystemExit(importlib.util.find_spec('black') is None)"; then \
		$(PYTHON) -m black .; \
	else \
		echo "black not installed; skip format"; \
	fi
	@if $(PYTHON) -c "import importlib.util; raise SystemExit(importlib.util.find_spec('ruff') is None)"; then \
		$(PYTHON) -m ruff check . --fix; \
	else \
		echo "ruff not installed; skip auto-fix"; \
	fi

coverage:
	@if $(PYTHON) -c "import importlib.util; raise SystemExit(importlib.util.find_spec('coverage') is None)"; then \
		$(PYTHON) -m coverage run -m pytest; \
		$(PYTHON) -m coverage report; \
	else \
		echo "coverage not installed; running pytest fallback"; \
		$(MAKE) test; \
	fi

docker-up:
	docker compose up -d

docker-down:
	docker compose down

seed:
	$(PYTHON) app/seed.py
