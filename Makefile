.PHONY: install format devrun devconsole help


requirements: ## Generate requirements.txt from requirements.in
	uv pip compile requirements.in > requirements.txt

install: ## Install packages from requirements.txt
	test -d .venv || uv venv --python $(cat .python-version)
	. .venv/bin/activate
	uv pip install -r requirements.txt
	python download_spacy_models.py
 
format: ## Format with ruff
	ruff format .
	ruff check --fix .

devrun: ## Run web backend
	litestar --app=backend.api_app:app run --reload-dir=backend

tui_devrun: ## Run CLI interface in DEV mode
	textual run --dev learn.py

tui_devconsole: ## Run dev console
	textual console  -x EVENT -x DEBUG

help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
