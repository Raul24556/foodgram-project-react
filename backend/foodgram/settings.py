import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка .env из корня проекта
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# Безопасность и режим
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,foodgram-eda.ddnsking.com').split(',')

# Добавляем CSRF_TRUSTED_ORIGINS для корректной обработки Origin
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:9000',
    'https://foodgram-eda.ddnsking.com',
]

# Настройки CSRF и сессий
CSRF_COOKIE_HTTPONLY = False  # Позволяем JS читать CSRF-токен (для админки не обязательно, но на всякий случай)
CSRF_COOKIE_SAMESITE = 'Lax'  # Разрешаем отправку куки на тот же сайт

# CORS
CORS_ALLOWED_ORIGINS = [
    origin for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,https://foodgram-eda.ddnsking.com').split(',')
    if origin.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_yasg',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'djoser',
    'django_filters',
    'users.apps.UsersConfig',
    'recipes.apps.RecipesConfig',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTH_USER_MODEL = 'users.User'
ROOT_URLCONF = 'foodgram.urls'
TEMPLATES_DIR = BASE_DIR / 'templates'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodgram.wsgi.application'

# Настройка базы данных
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'postgresql').lower()

if DATABASE_TYPE == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/data/db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'foodgram'),
            'USER': os.getenv('POSTGRES_USER', 'raul2455'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'viper2018'),
            'HOST': os.getenv('POSTGRES_HOST', 'db'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Статика и медиа
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = os.getenv('STATIC_ROOT', '/app/collected_static')
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/app/media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
PAGE_SIZE = int(os.getenv('PAGE_SIZE', '6'))
SHORT_LINK_LENGTH = int(os.getenv('SHORT_LINK_LENGTH', '6'))

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': PAGE_SIZE,
    'SEARCH_PARAM': 'name',
}

DJOSER = {
    'HIDE_USERS': False,
    'LOGIN_FIELD': 'email',
    'SERIALIZERS': {
        'user': 'api.serializers.UserListSerializer',
        'current_user': 'api.serializers.UserListSerializer',
    },
    'PERMISSIONS': {
        'user': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
        'user_list': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    },
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}
