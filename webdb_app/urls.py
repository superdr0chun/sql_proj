from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/servers/', views.api_servers, name='api_servers'),
    path('api/servers/<str:server_id>/databases/', views.api_databases, name='api_databases'),
    path('api/servers/<str:server_id>/databases/<str:db_name>/', views.api_database_info, name='api_database_info'),
    path('api/servers/<str:server_id>/databases/<str:db_name>/tables/', views.api_tables, name='api_tables'),
    path('api/servers/<str:server_id>/databases/<str:db_name>/tables/<str:table_name>/', views.api_table_info, name='api_table_info'),
    path('api/servers/<str:server_id>/databases/<str:db_name>/tables/<str:table_name>/rows/', views.api_rows, name='api_rows'),
    path('api/servers/<str:server_id>/databases/<str:db_name>/query/', views.api_query, name='api_query'),
]
