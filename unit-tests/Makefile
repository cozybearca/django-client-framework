.PHONY: defaults
defaults: alpine-base
	docker-compose run --rm dcf-test-alpine test -v2 dcf_test_suites

.PHONY: alpine-base
alpine-base:
	docker-compose build dcf-test-alpine

.PHONY: sh
sh: alpine-base
	docker-compose run --entrypoint sh dcf-test-alpine

%: Makefile
	docker-compose run --rm dcf-test-alpine test -v2 $@
