#!/usr/bin/env bash
# Запуск бэкенда и фронта одной командой: сборка React + Gunicorn.
# Использование: ./run.sh   (из корня проекта)

set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Сборка фронта только если билда ещё нет (на Render билд делают в Build Command)
if [ -f "$ROOT/front_football/package.json" ] && [ ! -f "$ROOT/front_football/build/index.html" ]; then
  [ -f "$ROOT/.env" ] && cp "$ROOT/.env" "$ROOT/front_football/.env"
  echo "Установка зависимостей фронта (npm install)..."
  (cd "$ROOT/front_football" && npm install) || { echo "Ошибка: npm install"; exit 1; }
  echo "Сборка фронта (npm run build)..."
  (cd "$ROOT/front_football" && npm run build) || { echo "Ошибка сборки фронта"; exit 1; }
  echo "Фронт собран."
elif [ -f "$ROOT/front_football/build/index.html" ]; then
  echo "Билд фронта уже есть, запуск сервера."
fi

# На Render PORT задан — используем gunicorn из PATH (установлен через pip в Build).
# Локально — venv в корне проекта, если есть.
if [ -n "${PORT}" ]; then
  GUNICORN="gunicorn"
elif [ -d "$ROOT/myenv/bin" ] && [ -x "$ROOT/myenv/bin/gunicorn" ]; then
  GUNICORN="$ROOT/myenv/bin/gunicorn"
elif [ -d "$ROOT/venv/bin" ] && [ -x "$ROOT/venv/bin/gunicorn" ]; then
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

# Миграции БД (на Render при каждом деплое создаётся чистая БД)
python manage.py migrate --noinput

# Начальные админы (Kotokogotka, Osip) — создаются только если ещё нет
python manage.py create_initial_superusers

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
