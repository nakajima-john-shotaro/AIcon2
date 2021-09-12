#!/bin/bash

VERSION="0.1.0"

IMAGE_NAME="aicon:${VERSION}"
BUILD_DIR=$(dirname $(readlink -f $0))

echo "${BUILD_DIR}"

docker build \
  -t ${IMAGE_NAME} \
  -f ${BUILD_DIR}/Dockerfile \
  --build-arg HOSTNAME=$(hostname) \
  ${BUILD_DIR}