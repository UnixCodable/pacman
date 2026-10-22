PYTHON ?= python3
UV ?= uv
MAIN ?= pac-man.py
CONFIG ?= config.json
MAZE_WHEEL := mazegenerator-00001/mazegenerator-2.1.0-py3-none-any.whl

.PHONY: install run debug clean lint lint-strict

install:
	$(UV) pip install "$(MAZE_WHEEL)"

run:
	$(PYTHON) "$(MAIN)" "$(CONFIG)"

debug:
	$(PYTHON) -m pdb "$(MAIN)" "$(CONFIG)"

clean:
	find . -type d \( -name '__pycache__' -o -name '.mypy_cache' -o -name '.pytest_cache' \) -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
