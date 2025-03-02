#!/bin/bash

set -e

sudo chmod 666 /var/run/docker.sock

docker pull docker.1ms.run/library/mysql:latest mysql:latest
docker pull docker.1ms.run/library/redis:latest redis:latest
docker pull docker.1ms.run/library/python:3.13-slim python:3.13-slim
