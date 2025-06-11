#!/bin/bash

set -e

overall_status=0

flake8 ./
flake8_status=$?
if [[ $flake8_status -ne 0 ]]; then
  overall_status=1
fi

pylint ./
pylint_status=$?
if [[ $pylint_status -ne 0 ]]; then
  overall_status=1
fi

mypy app/
mypy_status=$?
if [[ $mypy_status -ne 0 ]]; then
  overall_status=1
fi

bandit -r app/
bandit_status=$?
if [[ $bandit_status -ne 0 ]]; then
  overall_status=1
fi

if [[ $overall_status -ne 0 ]]; then
  echo "Code quality checks failed."
  exit 1
else
  echo "All code quality checks passed!"
  exit 0
fi