#!/bin/bash

set -e
redis-server redis.conf &
poetry run python api/api.py
