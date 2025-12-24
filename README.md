# Tourist Routes Service - Backend

Django REST API для веб-сервиса планирования туристических маршрутов в Казани.

## Технологии

- Django 4.2+
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- OpenAI API
- JWT Authentication

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения в `.env`:
```
SECRET_KEY=your-secret-key
DB_NAME=tourist_routes
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/1
OPENAI_API_KEY=your-openai-key
```

3. Примените миграции:
```bash
python manage.py migrate
```

4. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

5. Запустите сервер:
```bash
python manage.py runserver
```

## API Endpoints

- `/api/auth/` - Аутентификация
- `/api/attractions/` - Достопримечательности
- `/api/routes/` - Маршруты
- `/api/analytics/` - Аналитика

## Тестирование

```bash
pytest
```
