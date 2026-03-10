.PHONY: setup up down logs test clean status docker-ready

DOCKER_WAIT_TIMEOUT ?= 120
DOCKER_POLL_INTERVAL ?= 2

docker-ready:
ifeq ($(OS),Windows_NT)
	@powershell -NoProfile -ExecutionPolicy Bypass -File scripts/ensure-docker.ps1 -TimeoutSec $(DOCKER_WAIT_TIMEOUT) -PollIntervalSec $(DOCKER_POLL_INTERVAL)
else
	@docker info > /dev/null
endif

setup: docker-ready
	docker compose up --build -d
	@echo ""
	@echo "  DuckDB REST API  ->  http://localhost:9480"
	@echo "  Swagger UI       ->  http://localhost:9480/docs"
	@echo ""

up: docker-ready
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f api

test:
	docker compose exec api pytest tests/ -v

clean:
	docker compose down -v --rmi local

status:
	docker compose ps
