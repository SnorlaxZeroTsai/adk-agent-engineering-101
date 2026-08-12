PYTHON ?= python3

.PHONY: verify verify-project test-lab-01

verify: verify-project test-lab-01

verify-project:
	$(PYTHON) scripts/verify_project.py

test-lab-01:
	cd labs/01-agent-basics && $(PYTHON) -m unittest discover -s tests -v
