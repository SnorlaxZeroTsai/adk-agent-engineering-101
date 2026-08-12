PYTHON ?= python3
ADK_COMMIT := a56f6e13ae38296b608808c7a3b37efe4b8c862e
LAB_01 := $(CURDIR)/labs/01-agent-basics
LAB_02 := $(CURDIR)/labs/02-workflow-engineering
ADK_PYTHON ?= $(LAB_01)/.venv/bin/python

.PHONY: verify verify-project test-lab-01 test-lab-02 bootstrap-adk \
	verify-adk verify-workflows

verify: verify-project test-lab-01 test-lab-02

verify-project:
	$(PYTHON) scripts/verify_project.py

test-lab-01:
	cd labs/01-agent-basics && $(PYTHON) -m unittest discover -s tests -v

test-lab-02:
	cd labs/02-workflow-engineering && \
		$(PYTHON) -m unittest discover -s tests -v

bootstrap-adk:
	$(PYTHON) -m venv $(LAB_01)/.venv
	$(ADK_PYTHON) -m pip install "google-adk @ git+https://github.com/google/adk-python.git@$(ADK_COMMIT)"

verify-adk: verify-workflows
	test -x $(ADK_PYTHON)
	cd labs/01-agent-basics && .venv/bin/python -m unittest discover -s runtime_tests -v
	cd labs/01-agent-basics && .venv/bin/python scripts/run_runtime_trace.py >/dev/null

verify-workflows:
	test -x $(ADK_PYTHON)
	cd labs/02-workflow-engineering && \
		../01-agent-basics/.venv/bin/python \
		-m unittest discover -s runtime_tests -v
	cd labs/02-workflow-engineering && \
		../01-agent-basics/.venv/bin/python \
		scripts/run_workflow_traces.py >/dev/null
