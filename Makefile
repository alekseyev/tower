.PHONY: help


install: ## Install packages
	poetry install
	poetry run python cli.py download-spacy-models

format: ## Format with ruff
	ruff format .
	ruff check --fix .


help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
