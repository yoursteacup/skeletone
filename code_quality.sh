#!/bin/bash

set -e

# Run flake8, pylint, mypy and capture their exit statuses
flake8 ./
flake8_status=$?

pylint ./
pylint_status=$?

mypy app/
mypy_status=$?

bandit -r app/
bandit_status=$?

# Fail the job if any tool failed
if [[ $flake8_status -ne 0 || $pylint_status -ne 0 || $mypy_status -ne 0 || $bandit_status -ne 0 ]]; then
  echo "Code quality checks failed."
  exit 1
fi
