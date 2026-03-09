.PHONY: setup up down logs test clean status

setup:
	docker compose up --build -d
	@echo ""
	@echo "  DuckDB REST API  ->  http://localhost:9480"
	@echo "  Swagger UI       ->  http://localhost:9480/docs"
	@echo ""

up:
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
