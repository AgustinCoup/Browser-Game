from django.urls import path
from . import views

app_name = "characters"
urlpatterns = [
    path("crear/", views.crear_personaje,
         name="crear_personaje"),
]