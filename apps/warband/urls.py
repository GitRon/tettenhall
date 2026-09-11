from django.contrib.auth.decorators import login_not_required
from django.urls import path

from apps.warband.account import views as account_views
from apps.warband.faction import views as faction_views
from apps.warband.finance import views as finance_views
from apps.warband.item import views as item_views
from apps.warband.month import views as month_views
from apps.warband.quest import views as quest_views
from apps.warband.savegame import views as savegame_views
from apps.warband.skirmish import views as skirmish_views
from apps.warband.town.views.town_upgrade import TownUpgradeView, UpgradeBuildingView
from apps.warband.training import views as training_views
from apps.warband.warrior import views as warrior_views

# One namespace for the whole game. The route prefixes below are the ones the twelve app-level
# include() blocks used to supply, so every URL a player can hold keeps the path it had - the doubled
# "faction/faction/" and "warrior/warrior/" segments included.
app_name = "warband"

urlpatterns = [
    # Account
    path("account/login/", login_not_required(account_views.LoginView.as_view()), name="login-view"),
    path("account/logout/", account_views.LogoutView.as_view(), {}, name="logout-view"),
    path("account/dashboard/", account_views.DashboardView.as_view(), name="dashboard-view"),
    # Faction
    path(
        "faction/faction/<int:pk>/item/htmx",
        faction_views.FactionItemListView.as_view(),
        name="faction-item-list-htmx",
    ),
    path(
        "faction/faction/<int:pk>/warrior/htmx",
        faction_views.FactionWarriorListView.as_view(),
        name="faction-warrior-list-htmx",
    ),
    path(
        "faction/faction/<int:pk>/captured-warrior/htmx",
        faction_views.FactionCapturedWarriorListView.as_view(),
        name="faction-captured-warrior-list-htmx",
    ),
    path(
        "faction/faction/<int:pk>/pub/htmx",
        faction_views.FactionPubMercenaryListView.as_view(),
        name="pub-mercenary-list-htmx",
    ),
    # Above the detail route for readability only - "rivals" is not an int, so the two cannot collide
    path("faction/faction/rivals", faction_views.RivalFactionListView.as_view(), name="rival-faction-list-view"),
    path("faction/faction/<int:pk>", faction_views.FactionDetailView.as_view(), name="faction-detail-view"),
    path(
        "faction/faction/<int:pk>/draft/fyrd",
        faction_views.DraftWarriorFromFyrdView.as_view(),
        name="faction-draft-warrior-from-fyrd-view",
    ),
    # The warrior pk only: whose pub he is hired out of is the player's, read off the savegame
    path(
        "faction/faction/pub/mercenary/<int:pk>/recruit",
        faction_views.RecruitPubMercenaryView.as_view(),
        name="pub-mercenary-recruit-view",
    ),
    path("faction/faction/<int:pk>/attack", faction_views.FactionAttackView.as_view(), name="faction-attack-view"),
    path("faction/faction/<int:pk>/occupy", faction_views.FactionOccupyView.as_view(), name="faction-occupy-view"),
    path(
        "faction/faction/<int:pk>/costs/monthly",
        faction_views.MonthlyCostOverview.as_view(),
        name="faction-monthly-costs-view",
    ),
    path("faction/faction/<int:pk>/town-square", faction_views.TownSquareView.as_view(), name="town-square-view"),
    path(
        "faction/faction/<int:pk>/shop/item/htmx",
        faction_views.FactionShopItemListView.as_view(),
        name="shop-item-list-htmx",
    ),
    # The navbar counters, which are the player faction's own silver, roster, fights and wage bill
    path("faction/resource-bar/", faction_views.ResourceBarHtmxView.as_view(), name="resource-bar-htmx"),
    # Finance
    path("finance/", finance_views.TransactionListView.as_view(), name="transaction-list-view"),
    # Item
    path("item/<int:pk>/sell", item_views.ItemSellView.as_view(), name="item-sell-view"),
    path("item/<int:pk>/buy", item_views.ItemBuyView.as_view(), name="item-buy-view"),
    # Month
    path("month/finish/", month_views.FinishMonthView.as_view(), name="finish-month-view"),
    # Quest
    path("quest/<int:pk>/accept", quest_views.QuestAcceptView.as_view(), name="quest-accept-view"),
    # Savegame
    path("savegame/", savegame_views.SavegameListView.as_view(), name="savegame-list-view"),
    path("savegame/create/", savegame_views.SavegameCreateView.as_view(), name="savegame-create-view"),
    path("savegame/load/<int:pk>/", savegame_views.SavegameLoadView.as_view(), name="savegame-load-view"),
    # Skirmish
    path("skirmish/", skirmish_views.SkirmishListView.as_view(), name="skirmish-list-view"),
    path("skirmish/<int:pk>/", skirmish_views.SkirmishFightView.as_view(), name="skirmish-fight-view"),
    path(
        "skirmish/<int:pk>/finish-round/",
        skirmish_views.SkirmishFinishRoundView.as_view(),
        name="skirmish-finish-round-view",
    ),
    path(
        "skirmish/<int:skirmish_id>/battle/history/update/",
        skirmish_views.BattleHistoryUpdateHtmxView.as_view(),
        name="battle-history-update-htmx",
    ),
    path(
        "skirmish/<int:skirmish_id>/faction/<int:faction_id>/warrior-list/update/",
        skirmish_views.FactionWarriorListUpdateHtmxView.as_view(),
        name="faction-warrior-list-update-htmx",
    ),
    path(
        "skirmish/<int:pk>/round/update",
        skirmish_views.SkirmishRoundUpdateHtmxView.as_view(),
        name="skirmish-round-update-htmx",
    ),
    path(
        "skirmish/<int:pk>/fight-button/update",
        skirmish_views.SkirmishFightButtonUpdateHtmxView.as_view(),
        name="skirmish-fight-button-update-htmx",
    ),
    # Town
    path("town/", TownUpgradeView.as_view(), name="town-upgrade-view"),
    path(
        "town/building/upgrade/<str:building_type>",
        UpgradeBuildingView.as_view(),
        name="upgrade-building-view",
    ),
    # Training
    path("training/<int:pk>/edit", training_views.TrainingEditView.as_view(), name="training-edit-view"),
    # Warrior
    path("warrior/warrior/<int:pk>", warrior_views.WarriorDetailView.as_view(), name="warrior-detail-view"),
    path(
        "warrior/warrior/<int:pk>/captured/recruit/faction/<int:faction_id>",
        warrior_views.WarriorRecruitCapturedView.as_view(),
        name="warrior-recruit-captured-view",
    ),
    path(
        "warrior/warrior/<int:pk>/captured/enslave/faction/<int:faction_id>",
        warrior_views.WarriorEnslaveCapturedView.as_view(),
        name="warrior-enslave-captured-view",
    ),
    # The warrior pk only: which roster he is sent away from is the player's, read off the savegame
    path("warrior/warrior/<int:pk>/dismiss", warrior_views.DismissWarriorView.as_view(), name="warrior-dismiss-view"),
    path(
        "warrior/warrior/<int:pk>/partial-update/<str:htmx_attribute>",
        warrior_views.WarriorWeaponUpdateView.as_view(),
        name="warrior-partial-update-view",
    ),
]
