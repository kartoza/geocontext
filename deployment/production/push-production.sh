#!/usr/bin/env bash

if [[ -z "${GIT}" ]]; then
	GIT=kartoza
fi

if [[ -z "${REPO}" ]]; then
	REPO=geocontext
fi

if [[ -z "${BRANCH}" ]]; then
	BRANCH=master
fi

if [[ -z "${DOCKER}" ]]; then
	DOCKER=kartoza
fi

if [[ -z "${IMAGE}" ]]; then
	IMAGE=geocontext
fi

if [[ -z "${TAG}" ]]; then
	TAG=latest
fi

if [[ -z "${BUILD_ARGS}" ]]; then
	BUILD_ARGS="--no-cache"
fi

echo "Building from: git://github.com/${GIT}/${REPO}/${BRANCH}.git"
echo "Pushing to: https://hub.docker.com/r/${DOCKER}/${IMAGE}:${TAG}"

docker build \
	-f deployment/production/Dockerfile-prod \
	-t ${DOCKER}/${IMAGE}:${TAG} \
	--build-arg GIT=${GIT} \
	--build-arg REPO=${REPO} \
	--build-arg BRANCH=${BRANCH} \
	${BUILD_ARGS} \
	.
docker tag ${DOCKER}/${IMAGE}:latest ${DOCKER}/${IMAGE}:${TAG}
docker push ${DOCKER}/${IMAGE}:${TAG}
