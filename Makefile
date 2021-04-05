include .bootstrap.mk

DOCKER_IMAGE=zebradil/gimme-iphotos

bump-version:: ## Bump version to specified in V variable
	./make/bin/bump-version $(V)

docker-build:: ## Build container images
	./make/bin/docker-do just-build $(DOCKER_IMAGE)

docker-release:: ## Build and push container image
	./make/bin/docker-do build-and-push $(DOCKER_IMAGE)
