from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/servers/add', views.add_server, name='add_server'),
    path('api/servers', views.get_servers, name='get_servers'),
    path('api/server/<str:server_id>/tables', views.get_tables, name='get_tables'),
    path('api/server/<str:server_id>/table/<str:table_name>', views.get_table_info, name='get_table_info'),
    path('api/server/<str:server_id>/sql', views.execute_sql, name='execute_sql'),
    path('api/server/<str:server_id>/table/create', views.create_table, name='create_table'),
    path('api/server/<str:server_id>/table/<str:table_name>/delete', views.delete_table, name='delete_table'),
    path('api/server/<str:server_id>/table/<str:table_name>/insert', views.insert_row, name='insert_row'),
    path('api/server/<str:server_id>/delete', views.delete_server, name='delete_server'),
]
