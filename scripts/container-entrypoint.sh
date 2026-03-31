#!/bin/sh
set -eu

python scripts/wait_for_services.py
exec "$@"
