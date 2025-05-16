.PHONY: help init serve mcp test docker-up docker-down docker-build clean-cache clean-venv tag-release token
help:
	@echo "  help         - Show this help message"
	@echo "  init         - Initialize the uv virtual environment"
	@echo "  serve        - Start the Obsidian API server"
	@echo "  mcp          - Start the Model Context Protocol inspector"
	@echo "  test         - Run all tests"
	@echo "  docker-up    - Build and start the Docker containers"
	@echo "  docker-down  - Stop and remove the Docker containers"
	@echo "  docker-build - Build the Docker image"
	@echo "  clean-cache  - Clean up python cache directories"
	@echo "  clean-venv   - Clean up the uv virtual environment"
	@echo "  tag-release  - Create version tag and clean up branch after PR merge"
	@echo "  token        - Generate a secure bearer token"

init:
	uv venv

serve:
	uv run uvicorn app.main:app --reload

mcp:
	npx @modelcontextprotocol/inspector uv run python -m app.main

test:
	uv run pytest

docker-build:
	docker build -t obsidian-api .

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

tag:
	@if [ -z "$(BRANCH)" ] || [ -z "$(VERSION)" ]; then \
		echo "Usage: make tag BRANCH=<feature-branch> VERSION=<version-number>"; \
		echo "Example: make tag BRANCH=feature/new-auth VERSION=1.2.0"; \
		exit 1; \
	fi
	@echo "Creating version tag v$(VERSION) and cleaning up branch $(BRANCH)..."
	git checkout main
	git pull origin main
	git tag -a v$(VERSION) -m "Release version $(VERSION)"
	git push origin v$(VERSION)
	git branch -d $(BRANCH) || echo "Branch $(BRANCH) not found locally"
	@echo "Successfully created tag v$(VERSION) and cleaned up branch $(BRANCH)"

token:
	@python -c "import secrets; print(secrets.token_urlsafe(32))"
	