from django.urls import path
from . import views

urlpatterns = [
    path('api/servers/', views.servers, name='servers'),
    path('api/servers/<int:server_id>/', views.server_detail, name='server_detail'),
    path('api/servers/<int:server_id>/databases/', views.databases, name='databases'),
    path('api/servers/<int:server_id>/databases/<str:db_name>/', views.database_detail, name='database_detail'),
    path('api/servers/<int:server_id>/databases/<str:db_name>/tables/', views.tables, name='tables'),
    path('api/servers/<int:server_id>/databases/<str:db_name>/tables/create/', views.create_table, name='create_table'),
    path('api/servers/<int:server_id>/databases/<str:db_name>/tables/<str:table_name>/delete/', views.delete_table, name='delete_table'),
    path('api/servers/<int:server_id>/databases/<str:db_name>/tables/<str:table_name>/data/', views.table_data, name='table_data'),
    path('api/servers/<int:server_id>/databases/<str:db_name>/tables/<str:table_name>/insert/', views.insert_row, name='insert_row'),
    path('api/execute/', views.execute_sql, name='execute_sql'),
    path('', views.index, name='index'),
]
