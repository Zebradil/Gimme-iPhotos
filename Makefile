DOCKER_REGISTRY_HOST=docker.io
DOCKER_USERNAME=zebradil
DOCKER_NAME=gimme-iphotos

bump-version::
	./make/bin/bump-version $(V)

docker-build::
	./make/bin/docker-build

docker-push::
	./make/bin/docker-build
