DOCKER_IMAGE=zebradil/gimme-iphotos

bump-version::
	./make/bin/bump-version $(V)

docker-build::
	./make/bin/docker-do build $(DOCKER_IMAGE)

docker-push::
	./make/bin/docker-do push $(DOCKER_IMAGE)
