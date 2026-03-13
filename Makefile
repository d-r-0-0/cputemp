.PHONY: verify test lint fmt closeout install

verify: lint test

lint:
	.venv/bin/ruff check cputemp.py

fmt:
	.venv/bin/ruff format cputemp.py

test:
	.venv/bin/pytest tests/ -v

closeout:
	.venv/bin/python cantrips/session_closeout.py

install:
	.venv/bin/pip install -r requirements.txt

install-dev:
	.venv/bin/pip install -r requirements.txt ruff pytest
