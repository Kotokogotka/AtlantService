# Деплой на Render

Чтобы порт открывался сразу и деплой не отменялся по таймауту, **сборка фронта должна быть в Build Command**, а не в Start.

## В панели Render (Dashboard)

1. **Build Command** (обязательно укажите):
   ```bash
   pip install -r requirements.txt && cd front_football && npm install && npm run build && cd ../core && python manage.py collectstatic --noinput
   ```

2. **Start Command**:
   ```bash
   ./run.sh
   ```

3. **Root Directory** — оставьте пустым.

Скрипт `run.sh` при старте проверяет: если уже есть `front_football/build/index.html` (собран в Build), то npm не запускает и сразу стартует Gunicorn на порту `$PORT`.

## Через Blueprint (render.yaml)

В репозитории есть `render.yaml`. При создании сервиса через Blueprint эти команды подставятся автоматически.
