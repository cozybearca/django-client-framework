.PHONY: ubuntu-base
ubuntu-base:
	docker-compose build dcf-install-test-ubuntu


.PHONY: example
example: ubuntu-base
	docker-compose run dcf-test-example


.PHONY: example-ts
example-ts: example
	docker-compose run dcf-test-example-ts

.PHONY: format
format:
	sudo chmod a+w -R ..
	black ..

.PHONY: all
all: example example-ts format
