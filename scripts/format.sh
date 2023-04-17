#!/usr/bin/env bash

set -e
set -x

ruff CodeAutomation tests --fix
black CodeAutomation tests
isort CodeAutomation tests
