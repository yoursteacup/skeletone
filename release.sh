#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Использование:
  $0 <tag> "<сообщение релиза>" "<сообщение патча>"

Пример:
  $0 v1.2.0 "Release v1.2.0: improved API" \
           "Patch: fixed migration edge cases"
EOF
  exit 1
}

# Проверка аргументов
(( $# == 3 )) || usage
TAG=$1
RELEASE_MSG=$2
PATCH_MSG=$3

SCRIPT_NAME=$(basename "$0")

# --- Шаг 1: коммит релиза ---
echo "→ 1) Добавляем и коммитим релиз…"
git add .
echo
git diff --staged
echo
read -rp "Продолжить коммит релиза? [y/N] " yn
[[ $yn =~ ^[Yy] ]] || { echo "Отменено."; exit 1; }
git commit -m "$RELEASE_MSG"
git push

# --- Шаг 2: тег и пуш тегов ---
echo
echo "→ 2) Ставим тег $TAG и пушим…"
git tag -a "$TAG" -m "$RELEASE_MSG"
git push origin --tags

# --- Шаг 3: генерация патча ---
echo
echo "→ 3) Генерируем дифф-патч…"
# находим два последних тега по дате создания
LATEST_TAG=$(git tag --sort=-creatordate | head -n 1)
PREV_TAG=$(git tag --sort=-creatordate | head -n 2 | tail -n 1)
if [ -z "$LATEST_TAG" ] || [ -z "$PREV_TAG" ]; then
  echo "❗️ Ошибка: нужно минимум два тега для создания патча."
  exit 1
fi

mkdir -p patches
PATCH_FILE="patches/${PREV_TAG}_to_${LATEST_TAG}.patch"

git diff "$PREV_TAG" "$LATEST_TAG" \
  -- . ':!patches/' ':!README.md' ":!$SCRIPT_NAME" \
  > "$PATCH_FILE"
echo "✔ Патч сохранён: $PATCH_FILE"

# --- Шаг 4: коммит патча ---
echo
echo "→ 4) Коммитим патч…"
git add patches/
echo
git diff --cached
echo
read -rp "Продолжить коммит патча? [y/N] " yn
[[ $yn =~ ^[Yy] ]] || { echo "Отменено."; exit 1; }
git commit -m "$PATCH_MSG"
git push

echo
echo "🎉 Все шаги выполнены: релиз $TAG и патч опубликованы."