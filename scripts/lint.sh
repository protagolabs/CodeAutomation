#!/usr/bin/env bash

set -e
set -x

ruff CodeAutomation tests
black CodeAutomation tests --check --diff --color
isort CodeAutomation tests --check --diff
