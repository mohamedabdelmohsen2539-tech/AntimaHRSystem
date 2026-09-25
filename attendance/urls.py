from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("absence/", views.absence_page, name="absence_page"),
    path("absence/list/", views.absence_list_api, name="absence_list_api"),
    path("absence/recalculate/", views.recalculate_api, name="recalculate_api"),
]
