"""
Django settings for dailyfresh project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 把 apps 添加到 导包路径
import sys

sys.path.insert(1, os.path.join(BASE_DIR, 'apps'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5(&e!m%!52#mmjt8dbeer5d$35@hli$_yjf#m=eipn)py*1-i-'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',  # 富文本编辑器应用要注册
    'cart',
    'goods',
    'orders',
    'users',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'dailyfresh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'dailyfresh.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dailyfresh',
        'USER': 'root',
        'PASSWORD': 'mysql',
        'HOST': '192.168.21.134',  # mysql主服务器地址
        'PORT': '3306',
    },
    'slave': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dailyfresh',
        'USER': 'root',
        'PASSWORD': 'mysql',
        'HOST': '192.168.47.29',  # mysql从服务器地址
        'PORT': '3306',
    }
}

# 主从的读写分离配置
DATABASES_ROUTERS = ['utils.db_routers.MasterSlaveDBRouter']

# 固定的语法格式 (应用名.用户模型类名)
# 指定用来认证模型的应用 的路径
AUTH_USER_MODEL = 'users.User'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'

# 配置静态文件加载路径
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# 配置激活Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 导入邮件模块
EMAIL_HOST = 'smtp.163.com'  # 发送邮件的主机
EMAIL_PORT = 25  # 发邮件端口
EMAIL_HOST_USER = 'dragonax@163.com'  # 授权邮箱
EMAIL_HOST_PASSWORD = 'python6'  # 邮箱授权时获得的密码,非注册登录的密码
EMAIL_FROM = 'dragonax@163.com'  # 发件人抬头,就是发邮件用的地址

# 缓存(redis)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.21.134:6379/5",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Session
# 下面是 django-redis 的文档
# http://django-redis-chs.readthedocs.io/zh_CN/latest/#session-backend
# 指定 session 存在 redis 里
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# 如果用户没有登录 会去跳转到登录界面(从收货地址界面,跳转到登录界面)
LOGIN_URL = '/users/login'

# 配置Django自定义的存储系统
# DEFAULT_FILE_STORAGE = 'utils.fastdfs.storage.FastDFSStorage'
DEFAULT_FILE_STORAGE = 'utils.fastdfs.storage.FastDFSStorage'

# fastDFS的自定义配置
FDFS_CLIENT_CONF = os.path.join(BASE_DIR, 'utils/fastdfs/client.conf')  # 配置文件路径
SERVER_IP = 'http://192.168.21.134:8888'  # nginx服务器ip地址

# 富文本编辑器的配置
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',  # 丰富样式
    'width': 600,
    'height': 400,
}
