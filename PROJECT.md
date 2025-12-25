# Описание проекта: Веб-сервис планирования туристических маршрутов Казани

## Обзор проекта

Веб-сервис для планирования и описания туристических маршрутов в городе Казань. Система позволяет пользователям создавать персонализированные маршруты с использованием искусственного интеллекта (Perplexity API) и алгоритмической оптимизации, визуализировать их на интерактивных картах и анализировать статистику.

## Технологический стек

### Backend
- **Django 4.2.7** - веб-фреймворк
- **Django REST Framework 3.14.0** - REST API
- **PostgreSQL** - основная база данных
- **Redis 5.0.1** - кэширование, сессии, брокер для Celery
- **Celery 5.3.4** - асинхронные задачи
- **Perplexity AI** - генерация маршрутов через LLM
- **BeautifulSoup4, Selenium** - веб-скрапинг
- **Pandas, scikit-learn** - обработка данных и ML
- **Matplotlib, Seaborn** - визуализация данных

### Frontend
- **React 18.2.0** - UI библиотека
- **React Router 6.20.0** - маршрутизация
- **Yandex Maps API** - интерактивные карты
- **Axios 1.6.2** - HTTP клиент
- **Recharts 2.10.3** - графики и диаграммы
- **Vite 5.0.8** - сборщик

### Infrastructure
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - веб-сервер и прокси
- **Gunicorn** - WSGI сервер
- **Redis** - кэш и брокер сообщений

## Структура проекта

```
tourist-routes-service/
│
├── backend/                          # Django backend приложение
│   ├── accounts/                     # Модуль аутентификации и пользователей
│   │   ├── __init__.py
│   │   ├── admin.py                 # Админ-панель для пользователей
│   │   ├── apps.py
│   │   ├── models.py                # Модель User (расширенная)
│   │   ├── serializers.py           # Сериализаторы для API
│   │   ├── tests.py                 # Тесты модуля
│   │   ├── urls.py                  # URL маршруты
│   │   ├── views.py                 # API представления
│   │   └── migrations/              # Миграции БД
│   │       └── 0001_initial.py
│   │
│   ├── attractions/                  # Модуль достопримечательностей
│   │   ├── __init__.py
│   │   ├── admin.py                 # Админ-панель
│   │   ├── apps.py
│   │   ├── models.py                # Модели: Attraction, Category
│   │   ├── serializers.py           # Сериализаторы
│   │   ├── tests.py                 # Тесты
│   │   ├── urls.py                  # URL маршруты
│   │   ├── views.py                 # API представления
│   │   └── migrations/              # Миграции БД
│   │       └── 0001_initial.py
│   │
│   ├── routes/                       # Модуль маршрутов
│   │   ├── __init__.py
│   │   ├── admin.py                 # Админ-панель
│   │   ├── apps.py
│   │   ├── generators.py            # Генераторы маршрутов (LLM + алгоритмы)
│   │   ├── models.py                # Модели: Route, RouteAttraction, UserPreference
│   │   ├── serializers.py           # Сериализаторы
│   │   ├── tests.py                 # Тесты
│   │   ├── urls.py                  # URL маршруты
│   │   ├── views.py                 # API представления
│   │   └── migrations/              # Миграции БД
│   │       └── 0001_initial.py
│   │
│   ├── scraper/                      # Модуль веб-скрапинга
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── scraper.py               # Основной скрапер
│   │   ├── tasks.py                 # Celery задачи для скрапинга
│   │   ├── tests.py                 # Тесты
│   │   └── management/
│   │       └── commands/
│   │           └── scrape_attractions.py  # Django команда для скрапинга
│   │
│   ├── analytics/                    # Модуль аналитики
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── urls.py                  # URL маршруты
│   │   └── views.py                 # API представления для аналитики
│   │
│   ├── config/                       # Конфигурация Django проекта
│   │   ├── __init__.py              # Инициализация Celery
│   │   ├── asgi.py                  # ASGI конфигурация
│   │   ├── wsgi.py                  # WSGI конфигурация
│   │   ├── settings.py              # Настройки проекта
│   │   ├── urls.py                  # Главный URL конфиг
│   │   ├── celery.py                # Конфигурация Celery
│   │   ├── middleware.py            # Кастомные middleware
│   │   └── request_logging.py       # Middleware для логирования запросов
│   │
│   ├── manage.py                     # Django management скрипт
│   ├── pytest.ini                   # Конфигурация pytest
│   ├── media/                        # Медиа файлы (загруженные изображения)
│   └── staticfiles/                  # Статические файлы (собранные)
│
├── frontend/                         # React frontend приложение
│   ├── index.html                    # Главный HTML файл
│   ├── nginx.conf                    # Конфигурация Nginx
│   ├── package.json                  # Зависимости npm
│   ├── vite.config.js                # Конфигурация Vite
│   │
│   └── src/                          # Исходный код React
│       ├── main.jsx                  # Точка входа приложения
│       ├── App.jsx                    # Главный компонент
│       ├── App.css                    # Стили приложения
│       ├── index.css                  # Глобальные стили
│       │
│       ├── components/                # Переиспользуемые компоненты
│       │   ├── Navbar.jsx             # Навигационная панель
│       │   ├── Navbar.css
│       │   └── ProtectedRoute.jsx     # Компонент защищенного маршрута
│       │
│       ├── contexts/                  # React контексты
│       │   └── AuthContext.jsx        # Контекст аутентификации
│       │
│       ├── pages/                     # Страницы приложения
│       │   ├── Home.jsx               # Главная страница
│       │   ├── Home.css
│       │   ├── Login.jsx              # Страница входа
│       │   ├── Register.jsx          # Страница регистрации
│       │   ├── Auth.css               # Стили для страниц аутентификации
│       │   ├── RoutesList.jsx         # Список маршрутов
│       │   ├── RoutesList.css
│       │   ├── RouteDetail.jsx       # Детали маршрута (с картой)
│       │   ├── RouteDetail.css
│       │   ├── RouteCreate.jsx       # Создание маршрута
│       │   ├── RouteCreate.css
│       │   ├── Profile.jsx            # Профиль пользователя
│       │   ├── Profile.css
│       │   ├── Analytics.jsx         # Страница аналитики
│       │   └── Analytics.css
│       │
│       └── services/                  # Сервисы для работы с API
│           └── api.js                 # Axios клиент и API методы
│
├── docker-compose.yml                 # Docker Compose конфигурация
├── Dockerfile.backend                 # Dockerfile для backend
├── Dockerfile.frontend                # Dockerfile для frontend
├── requirements.txt                  # Python зависимости
├── README.md                         # Основная документация
├── PROJECT.md                        # Этот файл - описание проекта
└── manage.py                         # Django management (дубликат для удобства)
```

## Архитектура приложения

### Backend архитектура

#### Модели данных

**accounts.models.User**
- Расширенная модель пользователя Django
- Поля: email (уникальный), phone, avatar, bio
- Используется как USERNAME_FIELD для аутентификации

**attractions.models**
- `Category` - категории достопримечательностей (история, культура, архитектура и т.д.)
- `Attraction` - достопримечательности с координатами, описанием, рейтингом, ценой

**routes.models**
- `Route` - маршрут пользователя с метаданными (длительность, бюджет, расстояние)
- `RouteAttraction` - связь маршрута и достопримечательности с порядком посещения
- `UserPreference` - предпочтения пользователя для генерации маршрутов

#### API Endpoints

**Аутентификация** (`/api/auth/`)
- `POST /register/` - регистрация пользователя
- `POST /login/` - вход (получение JWT токенов)
- `POST /refresh/` - обновление access токена
- `GET /me/` - текущий пользователь
- `PUT /profile/` - обновление профиля

**Достопримечательности** (`/api/attractions/`)
- `GET /` - список с фильтрацией и поиском
- `GET /{id}/` - детали достопримечательности
- `GET /nearby/` - ближайшие достопримечательности по координатам

**Маршруты** (`/api/routes/`)
- `GET /` - список маршрутов пользователя
- `POST /` - создание маршрута вручную
- `GET /{id}/` - детали маршрута
- `PUT /{id}/` - обновление маршрута
- `DELETE /{id}/` - удаление маршрута
- `POST /generate/` - генерация маршрута через LLM/алгоритмы
- `POST /{id}/optimize/` - оптимизация порядка посещения
- `GET /favorites/` - избранные маршруты
- `POST /{id}/toggle_favorite/` - добавление/удаление из избранного

**Аналитика** (`/api/analytics/`)
- `GET /stats/` - общая статистика маршрутов
- `GET /user/` - статистика пользователя
- `GET /popular-attractions/` - популярные достопримечательности
- `GET /categories/popularity/` - популярность категорий
- `GET /attractions/by-category/` - достопримечательности по категориям
- `GET /trends/attractions/` - тренды использования
- `GET /categories/in-routes/` - распределение категорий в маршрутах

#### Генерация маршрутов

Система поддерживает три типа генерации:

1. **LLM-генерация** (`LLMRouteGenerator`)
   - Использует Perplexity API для создания описательных маршрутов
   - Анализирует описание пользователя и генерирует маршрут с актуальной информацией
   - Обогащает данные о достопримечательностях

2. **Алгоритмическая генерация** (`AlgorithmicRouteGenerator`)
   - Генерирует маршруты на основе фильтров (категории, бюджет, длительность)
   - Оптимизирует порядок посещения для минимизации расстояния
   - Использует алгоритм ближайшего соседа (Nearest Neighbor)

3. **Гибридная генерация**
   - Комбинация LLM и алгоритмической оптимизации
   - LLM выбирает достопримечательности, алгоритм оптимизирует порядок

#### Веб-скрапинг

Модуль `scraper` использует:
- **BeautifulSoup4** для парсинга HTML
- **Selenium** для динамического контента
- **Celery задачи** для периодического обновления данных
- **Perplexity API** для обогащения данных

### Frontend архитектура

#### Компоненты

**Навигация**
- `Navbar` - верхняя навигационная панель с меню
- `ProtectedRoute` - HOC для защиты маршрутов, требующих аутентификации

**Страницы**
- `Home` - главная страница с описанием сервиса
- `Login/Register` - страницы аутентификации
- `RoutesList` - список маршрутов пользователя
- `RouteDetail` - детали маршрута с интерактивной картой Яндекс
- `RouteCreate` - форма создания маршрута
- `Profile` - профиль пользователя
- `Analytics` - аналитика с графиками (Recharts)

#### Управление состоянием

- **AuthContext** - глобальное состояние аутентификации
- **LocalStorage** - хранение JWT токенов
- **Axios interceptors** - автоматическое обновление токенов

#### Карты

Используется нативный **Yandex Maps API**:
- Отображение маршрута на карте
- Маркеры достопримечательностей
- Линия маршрута (Polyline)
- Балуны с информацией при клике на маркеры

## Инфраструктура

### Docker Compose сервисы

1. **db** (PostgreSQL)
   - Образ: `postgres:15-alpine`
   - Порт: `5434:5432`
   - База данных: `tourist_routes`

2. **redis**
   - Образ: `redis:7-alpine`
   - Порт: `6379:6379`
   - Используется для:
     - Кэширования (база 1)
     - Сессий (база 1)
     - Celery broker (база 0)
     - Celery results (база 0)

3. **backend** (Django)
   - Сборка из `Dockerfile.backend`
   - Порт: `8000:8000`
   - Зависит от: db, redis
   - Команда: миграции + collectstatic + gunicorn

4. **frontend** (React)
   - Сборка из `Dockerfile.frontend`
   - Порт: `3001:80`
   - Nginx для статических файлов и проксирования API

5. **celery** (Celery Worker)
   - Сборка из `Dockerfile.backend`
   - Зависит от: db, redis, backend
   - Команда: `celery -A config worker -l info`

### Переменные окружения

**Backend (.env)**
```
SECRET_KEY=django-secret-key
DEBUG=True
DB_NAME=tourist_routes
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
PERPLEXITY_API_KEY=your-api-key
PERPLEXITY_MODEL=sonar-pro
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Frontend**
- `VITE_API_URL` - базовый URL API (по умолчанию `/api` для production)

## Использование Redis

Redis используется в проекте для:

1. **Кэширование Django** (база 1)
   - Кэширование запросов к БД
   - Ускорение работы API

2. **Хранение сессий** (база 1)
   - Сессии пользователей хранятся в Redis вместо БД
   - Быстрый доступ к данным сессий

3. **Celery Broker** (база 0)
   - Очередь задач для Celery
   - Асинхронное выполнение задач

4. **Celery Results Backend** (база 0)
   - Хранение результатов выполнения задач
   - Отслеживание статуса задач

## Потоки данных

### Создание маршрута

1. Пользователь заполняет форму на `/routes/create`
2. Frontend отправляет POST запрос на `/api/routes/generate/`
3. Backend выбирает тип генерации (LLM/алгоритмическая/гибридная)
4. Генератор создает маршрут с достопримечательностями
5. Маршрут сохраняется в БД
6. Возвращается ответ с данными маршрута
7. Frontend перенаправляет на `/routes/{id}`

### Отображение маршрута на карте

1. Frontend загружает данные маршрута через `/api/routes/{id}/`
2. Компонент `RouteDetail` получает координаты достопримечательностей
3. Инициализируется Yandex Maps через `window.ymaps.ready()`
4. Создаются маркеры для каждой достопримечательности
5. Добавляется линия маршрута (Polyline)
6. При клике на маркер открывается балун с информацией

### Веб-скрапинг достопримечательностей

1. Celery задача `scrape_attractions_task` запускается по расписанию
2. Выполняется Django команда `scrape_attractions`
3. Selenium открывает браузер и парсит данные
4. BeautifulSoup извлекает информацию из HTML
5. Данные обогащаются через Perplexity API
6. Достопримечательности сохраняются в БД

## Безопасность

- **JWT аутентификация** - токены доступа и обновления
- **CORS** - настроен для разрешенных доменов
- **CSRF** - отключен для API (используется JWT)
- **Валидация данных** - на уровне моделей и сериализаторов
- **Защищенные маршруты** - через `IsAuthenticated` permission
- **Хеширование паролей** - Django default

## Тестирование

- **pytest** - фреймворк для тестирования
- **pytest-django** - интеграция с Django
- **pytest-cov** - покрытие кода
- **factory-boy** - фабрики для тестовых данных

Запуск тестов:
```bash
cd backend
pytest                    # Все тесты
pytest --cov=. --cov-report=html  # С покрытием
```

## Развертывание

### Production

1. Настроить переменные окружения
2. Собрать Docker образы: `docker-compose build`
3. Запустить контейнеры: `docker-compose up -d`
4. Применить миграции: `docker-compose exec backend python manage.py migrate`
5. Собрать статические файлы: `docker-compose exec backend python manage.py collectstatic`
6. Создать суперпользователя: `docker-compose exec backend python manage.py createsuperuser`

### Мониторинг

- Логи: `docker-compose logs -f backend`
- Celery задачи: `docker-compose logs -f celery`
- Redis: `docker-compose exec redis redis-cli`

## Будущие улучшения

- [ ] Добавление кэширования результатов генерации маршрутов
- [ ] Оптимизация запросов к БД через select_related/prefetch_related
- [ ] Добавление WebSocket для real-time обновлений
- [ ] Экспорт маршрутов в PDF/GPX
- [ ] Мобильное приложение
- [ ] Интеграция с социальными сетями
- [ ] Система рекомендаций на основе ML

