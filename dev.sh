#!/bin/bash

set -e

sudo chmod 666 /var/run/docker.sock
docker-compose down --rm all || true
docker-compose up
