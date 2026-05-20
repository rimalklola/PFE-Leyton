# ============================================================================
# Leyton Automation Platform — Makefile
# One-command developer experience for local development and CI tasks.
# ============================================================================

.DEFAULT_GOAL := help

PYTHON   := python
PIP      := pip
SERVICES := folder-creator timesheet-consolidator handover-generator web-scraper
API_PORT := 8000

# ── Help ─────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  Leyton Automation Platform"
	@echo ""
	@echo "  make dev      Start the API locally with hot-reload"
	@echo "  make up       Start the full Docker stack"
	@echo "  make down     Stop the Docker stack"
	@echo "  make build    Build all Docker images"
	@echo "  make test     Run all service tests with coverage"
	@echo "  make lint     Lint all services"
	@echo "  make install  Install all dependencies"
	@echo "  make health   Check platform health"
	@echo "  make catalog  List discovered services"
	@echo "  make logs     Stream API logs"
	@echo "  make clean    Remove output files and cache"
	@echo ""

# ── Local development ─────────────────────────────────────────────────────────
.PHONY: dev
dev:
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port $(API_PORT) --reload

.PHONY: install
install:
	$(PIP) install -r api/requirements.txt
	@for svc in $(SERVICES); do \
		$(PIP) install -r services/$$svc/requirements.txt 2>/dev/null || true; \
	done

# ── Docker ───────────────────────────────────────────────────────────────────
.PHONY: up
up:
	docker compose up --build -d
	@echo "Web UI     → http://localhost:$(API_PORT)"
	@echo "Grafana    → http://localhost:3001  (admin / leyton2026)"
	@echo "Prometheus → http://localhost:9090"

.PHONY: down
down:
	docker compose down

.PHONY: build
build:
	docker compose build

.PHONY: logs
logs:
	docker compose logs -f api

# ── Quality ───────────────────────────────────────────────────────────────────
.PHONY: test
test:
	@for svc in $(SERVICES); do \
		echo ""; \
		echo "=== Testing $$svc ==="; \
		cd services/$$svc && \
		$(PYTHON) -m pytest test_$$(echo $$svc | tr '-' '_').py -v \
			--cov=. --cov-report=term-missing --cov-fail-under=80 && \
		cd ../..; \
	done

.PHONY: lint
lint:
	@for svc in $(SERVICES); do \
		echo "=== Linting $$svc ==="; \
		$(PYTHON) -m flake8 services/$$svc/main.py --max-line-length=120 --extend-ignore=E402; \
	done

# ── Platform utilities ────────────────────────────────────────────────────────
.PHONY: health
health:
	@curl -s http://localhost:$(API_PORT)/health | $(PYTHON) -m json.tool

.PHONY: catalog
catalog:
	@curl -s http://localhost:$(API_PORT)/services | $(PYTHON) -m json.tool

# ── History ───────────────────────────────────────────────────────────────────
.PHONY: history
history:
	@sqlite3 runs.db \
		"SELECT service, COALESCE(client_id,'—') as client, status, \
		        COALESCE(duration_ms||'ms','—') as duration, ran_at \
		 FROM runs ORDER BY ran_at DESC LIMIT 20;" \
		-column -header

# ── Cleanup ───────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@for svc in $(SERVICES); do rm -f services/$$svc/output/* 2>/dev/null || true; done
	@echo "Cleaned."
