from django.urls import path

from apps.skirmish import views

urlpatterns = [

    path('', views.SkirmishView.as_view(), name='skirmish-view'),
]
