#!/bin/bash
set -e

IMAGE="${IMAGE:-ghcr.io/forewalk/workshop}"
TAG="${TAG:-latest}"

cd "$(dirname "${BASH_SOURCE[0]}")/.."

docker build -t "$IMAGE:$TAG" .

echo "빌드 완료: $IMAGE:$TAG"
