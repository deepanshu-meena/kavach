.PHONY: install test run demo
install:
	pip install -e ".[dev]"
test:
	pytest -q
run:
	uvicorn kavach.api:app --reload
demo:
	python -m kavach.cli --demo
