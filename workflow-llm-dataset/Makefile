.PHONY: lint test build qa

lint:
	ruff check src tests scripts
	mypy src

test:
	pytest -q

build:
	python -m workflow_dataset.cli build --config configs/settings.yaml

qa:
	python -m workflow_dataset.cli qa --config configs/settings.yaml
