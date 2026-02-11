#!/usr/bin/env bash
# Запуск бэкенда и фронта одной командой: сборка React + Gunicorn.
# Использование: ./run.sh   (из корня проекта)

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Сборка фронта, если есть front_football
if [ -f "$ROOT/front_football/package.json" ]; then
  # Чтобы React подхватил REACT_APP_* при сборке, копируем .env из корня (если есть)
  [ -f "$ROOT/.env" ] && cp "$ROOT/.env" "$ROOT/front_football/.env"
  echo "Установка зависимостей фронта (npm install)..."
  (cd "$ROOT/front_football" && npm install) || { echo "Ошибка: npm install"; exit 1; }
  echo "Сборка фронта (npm run build)..."
  (cd "$ROOT/front_football" && npm run build) || { echo "Ошибка сборки фронта"; exit 1; }
  echo "Фронт собран."
fi

# Путь к gunicorn: venv в корне проекта
if [ -d "$ROOT/myenv/bin" ]; then
  GUNICORN="$ROOT/myenv/bin/gunicorn"
elif [ -d "$ROOT/venv/bin" ]; then
  GUNICORN="$ROOT/venv/bin/gunicorn"
else
  GUNICORN="gunicorn"
fi

if [ "$GUNICORN" = "gunicorn" ]; then
  command -v gunicorn &>/dev/null || { echo "Ошибка: Gunicorn не найден. Выполните: pip install gunicorn"; exit 1; }
else
  [ -x "$GUNICORN" ] || { echo "Ошибка: Gunicorn не найден по пути $GUNICORN. Выполните: pip install gunicorn"; exit 1; }
fi

cd "$ROOT/core"
export PYTHONPATH="$ROOT/core:${PYTHONPATH:-}"

# На Render порт задаётся через переменную PORT; локально используем 8000
PORT="${PORT:-8000}"
echo "Запуск Gunicorn на порту $PORT"
echo ""

exec "$GUNICORN" core.wsgi:application \
  --bind "0.0.0.0:${PORT}" \
  --workers 1 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
