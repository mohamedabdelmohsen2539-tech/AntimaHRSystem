"""
إعدادات مشروع تجريبي كامل عشان تقدر تشغل الـ HR وتشوفه في المتصفح.
لما تيجي تدمجه مع مشروع المبيعات/المخازن الأساسي، انقل الأجزاء المهمة
(INSTALLED_APPS الخاصة بالـ HR + UNFOLD + urls) لملف settings.py بتاع
مشروعك الأساسي بدل ما تستخدم الملف ده.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-CHANGE-ME-before-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "unfold",  # لازم يكون قبل django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # HR apps
    "employees",
    "attendance",
    "leaves",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,  # عشان Django يلاقي templates/employees و templates/attendance تلقائي
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# قاعدة بيانات SQLite للتجربة السريعة بس - في الإنتاج استخدم PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "ar"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Unfold — الألوان البنفسجي القريبة من هوية Kalia Flow
# ---------------------------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "نظام الموارد البشرية",
    "SITE_HEADER": "الموارد البشرية",
    "COLORS": {
        "primary": {
            "50": "250 245 255", "100": "243 232 255", "200": "233 213 255",
            "300": "216 180 254", "400": "192 132 252", "500": "168 85 247",
            "600": "147 51 234", "700": "126 34 206", "800": "107 33 168",
            "900": "88 28 135", "950": "59 7 100",
        },
    },
}
