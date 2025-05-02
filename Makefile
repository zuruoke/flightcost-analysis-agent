install:
	pip install uv
	uv sync

set-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make set-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ] && [ "$(ENV)" != "test" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production, test"; \
		exit 1; \
	fi
	@echo "Setting environment to $(ENV)"
	@bash -c "source scripts/set_env.sh $(ENV)"

prod:
	@echo "Starting server in production environment"
	@bash -c "source scripts/set_env.sh production && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

staging:
	@echo "Starting server in staging environment"
	@bash -c "source scripts/set_env.sh staging && ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

dev:
	@echo "Starting server in development environment"
	@bash -c "source scripts/set_env.sh development && uv run uvicorn app.main:app --reload --port 8000"

# Evaluation commands
eval:
	@echo "Running evaluation with interactive mode"
	@bash -c "source scripts/set_env.sh ${ENV:-development} && python -m evals.main --interactive"

eval-quick:
	@echo "Running evaluation with default settings"
	@bash -c "source scripts/set_env.sh ${ENV:-development} && python -m evals.main --quick"

eval-no-report:
	@echo "Running evaluation without generating report"
	@bash -c "source scripts/set_env.sh ${ENV:-development} && python -m evals.main --no-report"

lint:
	ruff check .

format:
	ruff format .

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache

docker-build:
	docker build -t fastapi-langgraph-template .

docker-build-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-build-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/build-docker.sh $(ENV)

docker-run:
	docker run -p 8000:8000 fastapi-langgraph-template

docker-run-env:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-run-env ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/run-docker.sh $(ENV)

docker-logs:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-logs ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/logs-docker.sh $(ENV)

docker-stop:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-stop ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	@./scripts/stop-docker.sh $(ENV)

# Docker Compose commands for the entire stack
docker-compose-up:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-up ENV=development|staging|production"; \
		exit 1; \
	fi
	@if [ "$(ENV)" != "development" ] && [ "$(ENV)" != "staging" ] && [ "$(ENV)" != "production" ]; then \
		echo "ENV is not valid. Must be one of: development, staging, production"; \
		exit 1; \
	fi
	APP_ENV=$(ENV) docker-compose up -d

docker-compose-down:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-down ENV=development|staging|production"; \
		exit 1; \
	fi
	APP_ENV=$(ENV) docker-compose down

docker-compose-logs:
	@if [ -z "$(ENV)" ]; then \
		echo "ENV is not set. Usage: make docker-compose-logs ENV=development|staging|production"; \
		exit 1; \
	fi
	APP_ENV=$(ENV) docker-compose logs -f

# Help
help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  install: Install dependencies"
	@echo "  set-env ENV=<environment>: Set environment variables (development, staging, production, test)"
	@echo "  run ENV=<environment>: Set environment and run server"
	@echo "  prod: Run server in production environment"
	@echo "  staging: Run server in staging environment"
	@echo "  dev: Run server in development environment"
	@echo "  eval: Run evaluation with interactive mode"
	@echo "  eval-quick: Run evaluation with default settings"
	@echo "  eval-no-report: Run evaluation without generating report"
	@echo "  test: Run tests"
	@echo "  clean: Clean up"
	@echo "  docker-build: Build default Docker image"
	@echo "  docker-build-env ENV=<environment>: Build Docker image for specific environment"
	@echo "  docker-run: Run default Docker container"
	@echo "  docker-run-env ENV=<environment>: Run Docker container for specific environment"
	@echo "  docker-logs ENV=<environment>: View logs from running container"
	@echo "  docker-stop ENV=<environment>: Stop and remove container"
	@echo "  docker-compose-up: Start the entire stack (API, Prometheus, Grafana)"
	@echo "  docker-compose-down: Stop the entire stack"
	@echo "  docker-compose-logs: View logs from all services"