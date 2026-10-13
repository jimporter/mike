BUILDDIR = build
TESTSUITES =

.PHONY: coverage
coverage:
	coverage erase
	PYTHONPATH=$(shell pwd)/test/scripts:$(PYTHONPATH) \
	COVERAGE_FILE=$(shell pwd)/.coverage \
	COVERAGE_PROCESS_START=$(shell pwd)/pyproject.toml \
	coverage run -m unittest discover
	coverage combine

.PHONY: test
test:
	python -m unittest discover

.PHONY: lint
lint:
	flake8 .

.PHONY: clean
clean:
	-rm -rf $(BUILDDIR)/*
