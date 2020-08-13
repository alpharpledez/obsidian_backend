from django.urls import path
from . import views

urlpatterns = [
    path('invite_members/', views.invite_members),
    path('deal_with_application/', views.deal_with_application),
    path('disband/', views.disband),
    path('get_team_name/',views.get_team_name),

    # just for debug
    path('isleader/', views.isleader),
    path('remove_member/',views.remove_member)
]
