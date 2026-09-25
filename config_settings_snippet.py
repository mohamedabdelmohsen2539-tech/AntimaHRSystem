"""
ده مش ملف settings.py كامل — ده الجزء اللي محتاج تضيفه/تدمجه مع settings.py
بتاع المشروع الأساسي (اللي فيه المبيعات والمخازن) عشان يشتغل عليه الـ HR
بنفس الشكل والألوان.
"""

INSTALLED_APPS = [
    "unfold",  # لازم يكون قبل django.contrib.admin
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",

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

LANGUAGE_CODE = "ar"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Unfold — نفس الهوية البصرية بتاعة Kalia Flow (بنفسجي/موف)
# ---------------------------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "نظام الموارد البشرية",
    "SITE_HEADER": "الموارد البشرية",
    "SITE_SYMBOL": "badge",
    "SHOW_LANGUAGES": True,
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",   # اللون الأساسي القريب من Kalia Flow
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": "الموارد البشرية",
                "items": [
                    {
                        "title": "الموظفين",
                        "icon": "badge",
                        "link": "/admin/employees/employee/",
                    },
                    {
                        "title": "استيراد من إكسيل",
                        "icon": "upload_file",
                        "link": "/hr/employees/import/",
                    },
                    {
                        "title": "الأقسام",
                        "icon": "apartment",
                        "link": "/admin/employees/department/",
                    },
                    {
                        "title": "طلبات الإجازات",
                        "icon": "event_available",
                        "link": "/admin/leaves/leaverequest/",
                    },
                    {
                        "title": "الأذونات",
                        "icon": "schedule",
                        "link": "/admin/leaves/permissionrequest/",
                    },
                    {
                        "title": "سجل البصمات",
                        "icon": "fingerprint",
                        "link": "/admin/attendance/attendancelog/",
                    },
                    {
                        "title": "ملخص الحضور والغياب",
                        "icon": "fact_check",
                        "link": "/admin/attendance/dailyattendancesummary/",
                    },
                ],
            },
        ],
    },
}

# ملحوظة عن FontAwesome:
# Unfold بيستخدم Material Symbols في السايدبار بتاعته بشكل أساسي.
# لو عايز تستخدم FontAwesome بدل كده في كل الصفحات المخصصة (زي صفحة
# استيراد الإكسيل وصفحات الإجازة/الإذن اللي شكلها ورقي)، أضف الرابط ده
# في template اسمه base_site.html بيعمل extend لـ admin/base.html:
#
# <link rel="stylesheet"
#   href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
