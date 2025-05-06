.PHONY: help init serve test docker-up docker-down docker-build clean-cache clean-venv release cleanup-branch token
help:
	@echo "  help         - Show this help message"
	@echo "  init         - Initialize the uv virtual environment"
	@echo "  serve        - Start the Obsidian API server"
	@echo "  test         - Run all tests"
	@echo "  docker-up    - Build and start the Docker containers"
	@echo "  docker-down  - Stop and remove the Docker containers"
	@echo "  docker-build - Build the Docker image"
	@echo "  clean-cache  - Clean up python cache directories"
	@echo "  clean-venv   - Clean up the uv virtual environment"
	@echo "  release      - Merge a feature branch and create a version tag"
	@echo "  cleanup-branch - Delete a feature branch locally and remotely"
	@echo "  token        - Generate a secure bearer token"

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

docker-build:
	docker build -t obsidian-api .

clean-cache:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 

clean-venv:
	deactivate 2>/dev/null || true
	rm -rf .venv
	uv venv

release:
	@if [ -z "$(BRANCH)" ] || [ -z "$(VERSION)" ]; then \
		echo "Usage: make release BRANCH=<feature-branch> VERSION=<version-number>"; \
		echo "Example: make release BRANCH=feature/new-auth VERSION=1.2.0"; \
		exit 1; \
	fi
	@echo "Merging $(BRANCH) into main and creating tag v$(VERSION)..."
	git checkout main
	git pull origin main
	git merge $(BRANCH)
	git tag -a v$(VERSION) -m "Release version $(VERSION)"
	git push origin main
	git push origin v$(VERSION)
	@echo "Successfully merged $(BRANCH) and created tag v$(VERSION)"

cleanup-branch:
	@if [ -z "$(BRANCH)" ]; then \
		echo "Usage: make cleanup-branch BRANCH=<feature-branch>"; \
		echo "Example: make cleanup-branch BRANCH=feature/new-auth"; \
		exit 1; \
	fi
	@echo "Cleaning up branch $(BRANCH)..."
	git checkout main
	git pull origin main
	git branch -d $(BRANCH) || echo "Branch $(BRANCH) not found locally"
	git push origin --delete $(BRANCH) || echo "Branch $(BRANCH) not found remotely"
	@echo "Successfully cleaned up branch $(BRANCH)"

token:
	@python -c "import secrets; print(secrets.token_urlsafe(32))"
	