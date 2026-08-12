PYTHON ?= python3
ADK_COMMIT := a56f6e13ae38296b608808c7a3b37efe4b8c862e
LAB_01 := $(CURDIR)/labs/01-agent-basics
LAB_02 := $(CURDIR)/labs/02-workflow-engineering
LAB_03 := $(CURDIR)/labs/03-multi-agent
LAB_04 := $(CURDIR)/labs/04-context-and-memory
LAB_05 := $(CURDIR)/labs/05-rag-engineering
LAB_06 := $(CURDIR)/labs/06-evaluation
LAB_07 := $(CURDIR)/labs/07-safety-hitl
LAB_08 := $(CURDIR)/labs/08-production-engineering
LAB_09 := $(CURDIR)/labs/09-pattern-catalog
LAB_10 := $(CURDIR)/labs/10-agent-garden-discovery
ADK_PYTHON ?= $(LAB_01)/.venv/bin/python

.PHONY: verify verify-project test-lab-01 test-lab-02 test-lab-03 \
	test-lab-04 test-lab-05 test-lab-06 bootstrap-adk verify-adk \
	verify-workflows verify-multi-agent verify-context-memory verify-rag \
	verify-evaluation test-lab-07 verify-safety-hitl test-lab-08 \
	verify-production test-lab-09 verify-pattern-catalog test-lab-10 \
	verify-agent-garden-discovery

verify: verify-project test-lab-01 test-lab-02 test-lab-03 test-lab-04 \
	test-lab-05 test-lab-06 test-lab-07 verify-production \
	verify-pattern-catalog verify-agent-garden-discovery

verify-project:
	$(PYTHON) scripts/verify_project.py

test-lab-01:
	cd labs/01-agent-basics && $(PYTHON) -m unittest discover -s tests -v

test-lab-02:
	cd labs/02-workflow-engineering && \
		$(PYTHON) -m unittest discover -s tests -v

test-lab-03:
	cd labs/03-multi-agent && \
		$(PYTHON) -m unittest discover -s tests -v

test-lab-04:
	cd labs/04-context-and-memory && \
		$(PYTHON) -m unittest discover -s tests -v

test-lab-05:
	cd labs/05-rag-engineering && \
		$(PYTHON) -m unittest discover -s tests -v

test-lab-06:
	cd labs/06-evaluation && \
		$(PYTHON) -m unittest discover -s tests -v

test-lab-07:
	cd labs/07-safety-hitl && \
		$(PYTHON) -m unittest discover -s tests -v

test-lab-08:
	cd labs/08-production-engineering && \
		$(PYTHON) -m unittest discover -s tests -v

verify-production: test-lab-08
	cd labs/08-production-engineering && \
		$(PYTHON) scripts/run_production_gate.py --variant baseline >/dev/null
	cd labs/08-production-engineering && \
		! $(PYTHON) scripts/run_production_gate.py --variant broken >/dev/null
	cd labs/08-production-engineering && \
		$(PYTHON) scripts/run_production_traces.py >/dev/null

test-lab-09:
	cd labs/09-pattern-catalog && \
		$(PYTHON) -m unittest discover -s tests -v

verify-pattern-catalog: test-lab-09
	cd labs/09-pattern-catalog && \
		$(PYTHON) scripts/run_pattern_gate.py --variant baseline >/dev/null
	cd labs/09-pattern-catalog && \
		! $(PYTHON) scripts/run_pattern_gate.py --variant broken >/dev/null
	cd labs/09-pattern-catalog && \
		$(PYTHON) scripts/run_pattern_traces.py >/dev/null

test-lab-10:
	cd labs/10-agent-garden-discovery && \
		$(PYTHON) -m unittest discover -s tests -v

verify-agent-garden-discovery: test-lab-10
	cd labs/10-agent-garden-discovery && \
		$(PYTHON) scripts/run_discovery_gate.py --variant baseline >/dev/null
	cd labs/10-agent-garden-discovery && \
		! $(PYTHON) scripts/run_discovery_gate.py --variant broken >/dev/null
	cd labs/10-agent-garden-discovery && \
		$(PYTHON) scripts/run_discovery_traces.py >/dev/null

bootstrap-adk:
	$(PYTHON) -m venv $(LAB_01)/.venv
	$(ADK_PYTHON) -m pip install "google-adk @ git+https://github.com/google/adk-python.git@$(ADK_COMMIT)"

verify-adk: verify-workflows verify-multi-agent verify-context-memory verify-rag \
	verify-safety-hitl verify-evaluation
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

verify-multi-agent:
	test -x $(ADK_PYTHON)
	cd labs/03-multi-agent && \
		../01-agent-basics/.venv/bin/python \
		-m unittest discover -s runtime_tests -v
	cd labs/03-multi-agent && \
		../01-agent-basics/.venv/bin/python \
		scripts/run_multi_agent_traces.py >/dev/null

verify-context-memory:
	test -x $(ADK_PYTHON)
	cd labs/04-context-and-memory && \
		../01-agent-basics/.venv/bin/python \
		-m unittest discover -s runtime_tests -v
	cd labs/04-context-and-memory && \
		../01-agent-basics/.venv/bin/python \
		scripts/run_context_memory_traces.py >/dev/null

verify-rag:
	test -x $(ADK_PYTHON)
	cd labs/05-rag-engineering && \
		../01-agent-basics/.venv/bin/python \
		-m unittest discover -s runtime_tests -v
	cd labs/05-rag-engineering && \
		../01-agent-basics/.venv/bin/python \
		scripts/run_rag_traces.py >/dev/null

verify-evaluation:
	test -x $(ADK_PYTHON)
	cd labs/06-evaluation && \
		../01-agent-basics/.venv/bin/python \
		-m unittest discover -s runtime_tests -v
	cd labs/06-evaluation && \
		../01-agent-basics/.venv/bin/python \
		scripts/run_eval_gate.py --variant baseline >/dev/null
	cd labs/06-evaluation && \
		! ../01-agent-basics/.venv/bin/python \
		scripts/run_eval_gate.py --variant broken >/dev/null
	cd labs/06-evaluation && \
		../01-agent-basics/.venv/bin/python \
		scripts/run_evaluation_traces.py >/dev/null

verify-safety-hitl:
	test -x $(ADK_PYTHON)
	cd labs/07-safety-hitl && \
		../01-agent-basics/.venv/bin/python \
		-m unittest discover -s runtime_tests -v
	cd labs/07-safety-hitl && \
		../01-agent-basics/.venv/bin/python \
		scripts/run_safety_hitl_traces.py >/dev/null
