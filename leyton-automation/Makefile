SERVICES = folder-creator timesheet-prefill belspo-extractor handover-generator \
           galileo-reporter web-scraper pdf-timesheet-extractor client-onboarding-generator

PYTHON = python

.PHONY: run-all test lint build api clean registry $(addprefix run-,$(SERVICES))

run-all:
	@for svc in $(SERVICES); do \
		echo "=== Running $$svc ==="; \
		cd services/$$svc && $(PYTHON) main.py; cd ../..; \
	done

$(addprefix run-,$(SERVICES)):
	cd services/$(@:run-%=%) && $(PYTHON) main.py

test:
	@for svc in $(SERVICES); do \
		test_file=services/$$svc/test_$$(echo $$svc | tr '-' '_').py; \
		if [ -f $$test_file ]; then \
			echo "=== Testing $$svc ==="; \
			cd services/$$svc && $(PYTHON) -m pytest $$(basename $$test_file) -v; cd ../..; \
		fi; \
	done

lint:
	@for svc in $(SERVICES); do \
		echo "=== Linting $$svc ==="; \
		$(PYTHON) -m flake8 services/$$svc/main.py --max-line-length=120 --extend-ignore=E402; \
	done

build:
	@for svc in $(SERVICES); do \
		echo "=== Building $$svc ==="; \
		docker build -t leyton-$$svc:latest services/$$svc; \
	done

api:
	cd api && $(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

clean:
	@for svc in $(SERVICES); do \
		rm -rf services/$$svc/output/*; \
		echo "Cleaned services/$$svc/output/"; \
	done

registry:
	@sqlite3 runs.db \
		"SELECT service, COALESCE(client_id,'—') as client, status, \
		        COALESCE(duration_ms||'ms','—') as duration, ran_at \
		 FROM runs ORDER BY ran_at DESC LIMIT 20;" \
		-column -header
