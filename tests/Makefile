.PHONY: ubuntu-base
ubuntu-base:
	docker-compose build dcf-test-ubuntu-base


.PHONY: example
example: ubuntu-base
	docker-compose run dcf-test-example
