from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('execute_query/', views.execute_query, name='execute_query'),
    path('get_tables/', views.get_tables, name='get_tables'),
    path('get_table_data/<str:table_name>/', views.get_table_data, name='get_table_data'),
    path('get_table_columns/<str:table_name>/', views.get_table_columns, name='get_table_columns'),
    path('add_record/<str:table_name>/', views.add_record, name='add_record'),
    path('update_record/<str:table_name>/<str:record_id>/<str:id_column>/', views.update_record, name='update_record'),
    path('delete_record/<str:table_name>/<str:record_id>/<str:id_column>/', views.delete_record, name='delete_record'),
    path('create_table/', views.create_table, name='create_table'),
    path('drop_table/<str:table_name>/', views.drop_table, name='drop_table'),
]
