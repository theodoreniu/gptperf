#!/bin/bash

set -e

sudo chmod 666 /var/run/docker.sock
docker-compose down || true
docker-compose up -d --scale worker_sql=15
