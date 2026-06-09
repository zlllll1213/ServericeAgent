.PHONY: dev test eval lint format coverage docker-up docker-down

dev:
	$(MAKE) -C serviceflow-agent-demo dev

test:
	$(MAKE) -C serviceflow-agent-demo test

eval:
	$(MAKE) -C serviceflow-agent-demo eval

lint:
	$(MAKE) -C serviceflow-agent-demo lint

format:
	$(MAKE) -C serviceflow-agent-demo format

coverage:
	$(MAKE) -C serviceflow-agent-demo coverage

docker-up:
	$(MAKE) -C serviceflow-agent-demo docker-up

docker-down:
	$(MAKE) -C serviceflow-agent-demo docker-down
