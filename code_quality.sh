#!/bin/bash

# Continue execution even if individual tools fail
set +e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print section header
print_header() {
    local tool_name="$1"
    local description="$2"
    echo -e "\n${CYAN}===========================================${NC}"
    echo -e "${BLUE}🔍 $tool_name${NC} - $description"
    echo -e "${CYAN}===========================================${NC}"
}

# Function to print result
print_result() {
    local tool_name="$1"
    local status="$2"
    if [[ $status -eq 0 ]]; then
        echo -e "${GREEN}✅ $tool_name: PASSED${NC}"
    else
        echo -e "${RED}❌ $tool_name: FAILED${NC}"
    fi
}

echo -e "${PURPLE}🚀 Starting code quality checks...${NC}\n"

# Run flake8
print_header "FLAKE8" "Style Guide Enforcement (PEP 8)"
flake8 ./
flake8_status=$?
print_result "FLAKE8" $flake8_status

# Run pylint
print_header "PYLINT" "Code Analysis & Quality Metrics"
pylint app/
pylint_status=$?
print_result "PYLINT" $pylint_status

# Run mypy
print_header "MYPY" "Static Type Checking"
mypy app/
mypy_status=$?
print_result "MYPY" $mypy_status

# Run bandit
print_header "BANDIT" "Security Vulnerability Scanner"
bandit -r app/
bandit_status=$?
print_result "BANDIT" $bandit_status

# Summary
echo -e "\n${CYAN}===========================================${NC}"
echo -e "${BLUE}📊 SUMMARY${NC}"
echo -e "${CYAN}===========================================${NC}"

print_result "FLAKE8 (Style)" $flake8_status
print_result "PYLINT (Quality)" $pylint_status
print_result "MYPY (Types)" $mypy_status
print_result "BANDIT (Security)" $bandit_status

# Fail the job if any tool failed
if [[ $flake8_status -ne 0 || $pylint_status -ne 0 || $mypy_status -ne 0 || $bandit_status -ne 0 ]]; then
    echo -e "\n${RED}💥 Code quality checks failed!${NC}"
    echo -e "${YELLOW}📝 Please fix the issues above before proceeding.${NC}"
    exit 1
else
    echo -e "\n${GREEN}🎉 All code quality checks passed!${NC}"
    echo -e "${GREEN}✨ Your code is ready for deployment.${NC}"
fi