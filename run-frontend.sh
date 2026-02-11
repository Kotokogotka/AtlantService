#!/usr/bin/env bash
# Запуск React-фронта одной командой из корня проекта.
# После запуска откройте в браузере: http://localhost:3000

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/front_football"

echo "Запуск фронта — откройте в браузере: http://localhost:3000"
echo ""

exec npm start
