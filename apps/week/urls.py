from django.urls import path

from apps.week import views

urlpatterns = [
    path("finish/", views.FinishWeekView.as_view(), name="finish-week-view"),
]
