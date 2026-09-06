from django.urls import path

from apps.month import views

urlpatterns = [
    path("finish/", views.FinishMonthView.as_view(), name="finish-month-view"),
]
