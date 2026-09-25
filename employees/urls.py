from django.urls import path

from . import views

app_name = "employees"

urlpatterns = [
    path("import/", views.import_employees_page, name="import_page"),
    path("import/preview/", views.import_employees_preview, name="import_preview"),
    path("import/commit/", views.import_employees_commit, name="import_commit"),
    path("search/", views.employees_live_search, name="live_search"),
]
