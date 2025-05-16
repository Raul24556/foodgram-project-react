# Foodgram - Продуктовый помощник

Foodgram — это веб-приложение, которое позволяет пользователям публиковать рецепты, добавлять их в избранное, подписываться на других пользователей и формировать список покупок для выбранных рецептов. Проект реализован с использованием Django (бэкенд) и React (фронтенд).

## Основные возможности
### Рецепты:
- Публикация рецептов с изображениями, описанием и списком ингредиентов.
- Фильтрация рецептов по тегам, автору и избранному.
- Добавление рецептов в избранное.
- Формирование списка покупок на основе выбранных рецептов.

### Пользователи:
- Регистрация и аутентификация.
- Подписка на других пользователей.
- Просмотр рецептов других пользователей.

### API:
- Полноценное REST API для взаимодействия с бэкендом.
- Документация API доступна по адресу: `/api/docs/`.

## Технологии
### Бэкенд:
- Python 3.9
- Django 4.2.18
- Django REST Framework
- PostgreSQL
- Gunicorn
- Nginx

### Фронтенд:
- React
- Webpack

### Инфраструктура:
- Docker
- Docker Compose

## Установка и запуск проекта
### 1. Клонирование репозитория
```bash
git clone https://github.com/ваш-username/foodgram-project-react.git
cd foodgram-project-react/infra
```

### 2. Настройка переменных окружения
Создайте файл `.env` в папке `infra` и добавьте:
```env
SECRET_KEY=ваш-секретный-ключ
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

### 3. Запуск контейнеров
```bash
docker-compose up
```

### 4. Применение миграций
```bash
docker-compose exec backend python manage.py migrate
```

### 5. Создание суперпользователя
```bash
docker-compose exec backend python manage.py createsuperuser
```

### 6. Загрузка тестовых данных (опционально)
```bash
docker-compose exec backend python manage.py loaddata fixtures.json
```

## Доступ к приложению
- Фронтенд: `http://<ваш-домен>`
- Админка: `http://<ваш-домен>/admin`
- API: `http://<ваш-домен>/api/docs/`

## Автор
- **Кирилл Мендрин**
- GitHub: [Raul24556](https://github.com/Raul24556)
- Email: kirillmendrin245@yandex.com

## Ссылка на проект
Доступен по адресу: https://foodgram-eda.ddnsking.com/
