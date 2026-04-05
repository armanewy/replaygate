PYTHON ?= python

.PHONY: install lint format test verify-example-pass verify-example-fail report-example

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev,temporal]"

lint:
	$(PYTHON) -m ruff check replaygate tests examples

format:
	$(PYTHON) -m ruff format replaygate tests examples

test:
	$(PYTHON) -m pytest

verify-example-pass:
	$(PYTHON) -m replaygate.cli verify --config examples/temporal/replaygate.pass.yaml

verify-example-fail:
	$(PYTHON) -m replaygate.cli verify --config examples/temporal/replaygate.yaml

report-example:
	$(PYTHON) -m replaygate.cli report --input examples/temporal/artifacts/report.json --html examples/temporal/artifacts/report.html
