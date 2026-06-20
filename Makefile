.PHONY: install playground dev generate-traces grade

install:
	uv sync

playground:
	uv run adk web --port 8501

generate-traces:
	uv run python tests/eval/generate_traces.py

grade:
	uv run agents-cli eval grade --traces artifacts/traces/generated_traces.json --config tests/eval/eval_config.yaml

dev:
	uv run python expense_agent/fast_api_app.py
