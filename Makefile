PYTHON ?= python3
SKILL  := skills/ultimate-seo

.PHONY: test lint unit package eval clean

test: lint unit

lint:
	$(PYTHON) tools/validate_skill.py

unit:
	$(PYTHON) -m unittest discover -s tests

# Zip for Claude.ai / Claude Desktop upload (evals are dev-only, so they're left out).
package: lint
	@mkdir -p dist
	@rm -f dist/ultimate-seo.zip
	cd skills && zip -qr ../dist/ultimate-seo.zip ultimate-seo -x 'ultimate-seo/evals/*' '*/__pycache__/*' '*.pyc' '*.DS_Store'
	@echo "Built dist/ultimate-seo.zip"

# End-to-end evals: real, billed model runs via Claude Code.
eval:
	cd $(SKILL) && claude plugin eval . --allow-tools Write,Edit,Bash --scaffold

clean:
	rm -rf dist $(SKILL)/evals/results
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
