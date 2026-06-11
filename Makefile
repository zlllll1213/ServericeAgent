.PHONY: dev test eval lint format coverage docker-up docker-down

dev:
	$(MAKE) -C serviceflow-agent-console dev

test:
	$(MAKE) -C serviceflow-agent-console test

eval:
	$(MAKE) -C serviceflow-agent-console eval

lint:
	$(MAKE) -C serviceflow-agent-console lint

format:
	$(MAKE) -C serviceflow-agent-console format

coverage:
	$(MAKE) -C serviceflow-agent-console coverage

docker-up:
	$(MAKE) -C serviceflow-agent-console docker-up

docker-down:
	$(MAKE) -C serviceflow-agent-console docker-down
