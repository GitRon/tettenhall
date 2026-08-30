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
    # Above the detail route for readability only - "rivals" is not an int, so the two cannot collide
    path("faction/rivals", views.RivalFactionListView.as_view(), name="rival-faction-list-view"),
    path("faction/<int:pk>", views.FactionDetailView.as_view(), name="faction-detail-view"),
    path(
        "faction/<int:pk>/draft/fyrd",
        views.DraftWarriorFromFyrdView.as_view(),
        name="faction-draft-warrior-from-fyrd-view",
    ),
    # The warrior pk only: whose pub he is hired out of is the player's, read off the savegame
    path(
        "faction/pub/mercenary/<int:pk>/recruit",
        views.RecruitPubMercenaryView.as_view(),
        name="pub-mercenary-recruit-view",
    ),
    path("faction/<int:pk>/attack", views.FactionAttackView.as_view(), name="faction-attack-view"),
    path("faction/<int:pk>/occupy", views.FactionOccupyView.as_view(), name="faction-occupy-view"),
    path("faction/<int:pk>/costs/monthly", views.MonthlyCostOverview.as_view(), name="faction-monthly-costs-view"),
    path("faction/<int:pk>/town-square", views.TownSquareView.as_view(), name="town-square-view"),
    path("faction/<int:pk>/shop/item/htmx", views.FactionShopItemListView.as_view(), name="shop-item-list-htmx"),
]
