from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/servers/', views.get_servers, name='get_servers'),
    path('api/servers/add/', views.add_server, name='add_server'),
    path('api/servers/delete/', views.delete_server, name='delete_server'),
    path('api/databases/', views.get_databases, name='get_databases'),
    path('api/databases/create/', views.create_database, name='create_database'),
    path('api/databases/drop/', views.drop_database, name='drop_database'),
    path('api/tables/', views.get_tables, name='get_tables'),
    path('api/tables/create/', views.create_table, name='create_table'),
    path('api/tables/drop/', views.drop_table, name='drop_table'),
    path('api/tables/info/', views.get_table_info, name='get_table_info'),
    path('api/tables/data/', views.get_table_data, name='get_table_data'),
    path('api/query/execute/', views.execute_query, name='execute_query'),
    path('api/rows/insert/', views.insert_row, name='insert_row'),
    path('api/rows/update/', views.update_row, name='update_row'),
    path('api/rows/delete/', views.delete_row, name='delete_row'),
]
