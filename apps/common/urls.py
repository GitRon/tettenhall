from django.urls import path

from apps.common import views

urlpatterns = [
    path("resource-bar/", views.ResourceBarHtmxView.as_view(), name="resource-bar-htmx"),
]
