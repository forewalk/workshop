#!/bin/bash
set -e

IMAGE="${IMAGE:-ghcr.io/forewalk/workshop}"
TAG="${TAG:-latest}"

docker push "$IMAGE:$TAG"

echo "푸시 완료: $IMAGE:$TAG"
