from django.urls import path
from dashboard import views

urlpatterns = [
    path('', views.home, name="home"),
    path('statistics/', views.statistics, name="statistics"),
    path('demand-forecast/', views.demand_forecast, name="demand-forecast"),
    path('cost-calculation/', views.cost_calculation, name="cost-calculation"),
    path('capacity-planning/', views.capacity_planning, name="capacity-planning"),
    path('update-data/', views.update_data, name="update-data"),
]