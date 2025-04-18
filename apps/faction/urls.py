from django.urls import path

from apps.faction import views

urlpatterns = [
    path("faction/<int:pk>/item/htmx", views.FactionItemListView.as_view(), name="faction-item-list-htmx"),
    path("faction/<int:pk>/warrior/htmx", views.FactionWarriorListView.as_view(), name="faction-warrior-list-htmx"),
    path(
        "faction/<int:pk>/captured-warrior/htmx",
        views.FactionCapturedWarriorListView.as_view(),
        name="faction-captured-warrior-list-htmx",
    ),
    path("faction/<int:pk>", views.FactionDetailView.as_view(), name="faction-detail-view"),
    path(
        "faction/<int:pk>/draft/fyrd",
        views.DraftWarriorFromFyrdView.as_view(),
        name="faction-draft-warrior-from-fyrd-view",
    ),
    path("faction/<int:pk>/costs/monthly", views.MonthlyCostOverview.as_view(), name="faction-monthly-costs-view"),
    path("faction/<int:pk>/town-square", views.TownSquareView.as_view(), name="town-square-view"),
    path("faction/<int:pk>/shop/item/htmx", views.FactionShopItemListView.as_view(), name="shop-item-list-htmx"),
]
