.PHONY: help init serve test docker-up docker-down clean-cache clean-venv
help:
	@echo "  help         - Show this help message"
	@echo "  init         - Initialize the uv virtual environment"
	@echo "  serve        - Start the Obsidian API server"
	@echo "  test         - Run all tests"
	@echo "  docker-up    - Build and start the Docker containers"
	@echo "  docker-down  - Stop and remove the Docker containers"
	@echo "  clean-cache  - Clean up python cache directories"
	@echo "  clean-venv   - Clean up the uv virtual environment"

init:
	uv venv

serve:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down --rmi all

clean-cache:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 

clean-venv:
	deactivate 2>/dev/null || true
	rm -rf .venv
	uv venv