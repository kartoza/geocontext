#!/usr/bin/env bash

if [ -z "$REPO_NAME" ]; then
	REPO_NAME=kartoza
fi

if [ -z "$IMAGE_NAME" ]; then
	IMAGE_NAME=geocontext
fi

if [ -z "$TAG_NAME" ]; then
	TAG_NAME=latest
fi

if [ -z "$BUILD_ARGS" ]; then
	BUILD_ARGS="--no-cache"
fi

# Build Args Environment

if [ -z "$BRANCH" ]; then
	BRANCH=master
fi

echo "BRANCH=${BRANCH}"

echo "Build: $REPO_NAME/$IMAGE_NAME:$TAG_NAME"

cd production
docker build -f Dockerfile-prod -t ${REPO_NAME}/${IMAGE_NAME} --build-arg BRANCH=${BRANCH} ${BUILD_ARGS} .
docker tag ${REPO_NAME}/${IMAGE_NAME}:latest ${REPO_NAME}/${IMAGE_NAME}:${TAG_NAME}
docker push ${REPO_NAME}/${IMAGE_NAME}:${TAG_NAME}
