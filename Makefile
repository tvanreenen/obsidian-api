.PHONY: help run test clean
help:
	@echo "Available targets:"
	@echo "  help        - Show this help message"
	@echo "  run         - Start the Obsidian API server"
	@echo "  test        - Run all tests"
	@echo "  clean       - Clean up temporary directories"

run:
	@echo "Starting Obsidian API server..."
	uv run uvicorn app.main:app --reload

test:
	@echo "Running all tests..."
	uv run pytest

clean:
	@echo "Cleaning up temporary directories..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 