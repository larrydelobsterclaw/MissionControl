.PHONY: test lint smoke

test:
	pytest -q

lint:
	python -m compileall mission_control

smoke:
	mc init
	mc project create "Demo Project" --goal "Ship MVP"
	mc task create --project demo-project --title "Scaffold" --desc "Create files" --priority 2 --model-hint coder
	mc status --project demo-project
	mc digest
