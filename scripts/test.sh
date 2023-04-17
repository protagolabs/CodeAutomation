#!/usr/bin/env bash

set -e
set -x

pytest tests --cov CodeAutomation  --cov-report html:cov_html --cov-report term
