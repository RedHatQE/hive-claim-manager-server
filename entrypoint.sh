#!/bin/bash

set -e
redis-server &
poetry run python api/api.py
