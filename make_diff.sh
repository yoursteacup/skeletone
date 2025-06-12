#!/bin/bash

# Название скрипта (чтобы исключить из diff)
SCRIPT_NAME=$(basename "$0")

# Получаем последние два тега (сортировка по времени)
TAGS=($(git tag --sort=-creatordate))
LATEST_TAG=${TAGS[0]}
PREV_TAG=${TAGS[1]}
echo "📌 Сравниваем теги: $PREV_TAG → $LATEST_TAG"
PATCH_NAME="${PREV_TAG}_to_${LATEST_TAG}.patch"

# Выполняем git diff с исключением определённых путей
git diff "$PREV_TAG" "$LATEST_TAG" -- . ':!patches/' ':!README.md' ":!$SCRIPT_NAME" > patches/$PATCH_NAME