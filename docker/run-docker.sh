#!/bin/bash
HOST_SD=$(dirname $(dirname $(readlink -f $0)))/aicon

VERSION="0.0.2"

IMAGE_NAME="aicon:${VERSION}"

clear
echo -e "Run \`sudo xhost +local:root\` on the host to use graphical applications."
 
docker run \
  --rm -it \
  --gpus all \
  --env "DISPLAY=${DISPLAY}" \
  --privileged \
  --shm-size=11gb \
  --net=host \
  --user="$(id -u):$(id -g)" \
  --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  --volume="${HOST_SD}:/workspace:rw" \
  --name="aicon" \
  ${IMAGE_NAME} \
  bash