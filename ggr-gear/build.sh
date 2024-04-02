#!/bin/sh

# Check that appropriate proxy variables are set when needed.
# It may be necessary to restart the docker service.
# service docker restart
# sudo /bin/systemctl restart docker.service

DOCKER_BUILDKIT=1 docker build --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') -t ggr-gear:latest --build-arg VERSION="1.0.0_1.0.4" -f Dockerfile .
