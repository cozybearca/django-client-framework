.PHONY: ubuntu-base
ubuntu-base:
	docker-compose build dcf-test-ubuntu-base


.PHONY: example
example: ubuntu-base
	docker-compose run dcf-test-example
	tar -czvf dcf-backend-example/dcf-backend-example-proj.tar.gz dcf-backend-example/dcf-backend-example-proj


.PHONY: example-ts
example-ts: example
	docker-compose run dcf-test-example-ts

