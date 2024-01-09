"""tettenhall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the "include()" function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Default
    path("admin/", admin.site.urls),
    # Custom
    path("", RedirectView.as_view(pattern_name="account:dashboard-view", permanent=False)),
    path("account/", include(("apps.account.urls", "apps.account"), namespace="account")),
    path("faction/", include(("apps.faction.urls", "apps.faction"), namespace="faction")),
    path("finance/", include(("apps.finance.urls", "apps.finance"), namespace="finance")),
    path("item/", include(("apps.item.urls", "apps.item"), namespace="item")),
    path("marketplace/", include(("apps.marketplace.urls", "apps.marketplace"), namespace="marketplace")),
    path("quest/", include(("apps.quest.urls", "apps.quest"), namespace="quest")),
    path(
        "skirmish/",
        include(("apps.skirmish.urls", "apps.skirmish"), namespace="skirmish"),
    ),
    path("training/", include(("apps.training.urls", "apps.training"), namespace="training")),
    path("warrior/", include(("apps.warrior.urls", "apps.week"), namespace="warrior")),
    path("week/", include(("apps.week.urls", "apps.week"), namespace="week")),
]
