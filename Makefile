.PHONY: install format devrun devconsole help


install: ## Install packages from requirements.txt
	test -d .venv || uv venv --python $(cat .python-version)
	. .venv/bin/activate
	uv sync
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

flet_run: ## run flet based GUI
	PYTHONPATH="." flet run -d -r flet_ui

admin: ## Run admin backend
	python -m backend.admin.main

help: ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
