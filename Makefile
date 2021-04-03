include .bootstrap.mk

DOCKER_IMAGE=zebradil/gimme-iphotos

bump-version:: ## Bump version to specified in V variable
	./make/bin/bump-version $(V)

docker-build:: ## Build container image
	./make/bin/docker-do build $(DOCKER_IMAGE)

docker-push:: ## Push container image
	./make/bin/docker-do push $(DOCKER_IMAGE)
