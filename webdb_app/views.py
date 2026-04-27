from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .database import db_manager


def index(request):
    """Главная страница с интерфейсом СУБД"""
    return render(request, 'webdb_app/index.html')


@csrf_exempt
def api_servers(request):
    """API для работы с серверами"""
    if request.method == 'GET':
        servers = db_manager.list_servers()
        return JsonResponse({'servers': servers})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        server_id = data.get('id', 'server_' + str(len(db_manager.servers)))
        connection_string = data.get('connection_string', '')
        
        if not connection_string:
            return JsonResponse({'success': False, 'error': 'Connection string required'})
        
        success = db_manager.add_server(server_id, connection_string)
        if success:
            return JsonResponse({'success': True, 'server_id': server_id})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to connect'})
    
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        server_id = data.get('id')
        if server_id and server_id != 'default':
            db_manager.remove_server(server_id)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Cannot delete default server'})


@csrf_exempt
def api_databases(request, server_id):
    """API для работы с базами данных"""
    if request.method == 'GET':
        databases = db_manager.list_databases(server_id)
        return JsonResponse({'databases': databases})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        db_name = data.get('name')
        if not db_name:
            return JsonResponse({'success': False, 'error': 'Database name required'})
        
        success, message = db_manager.create_database(server_id, db_name)
        return JsonResponse({'success': success, 'message': message})
    
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        db_name = data.get('name')
        if not db_name:
            return JsonResponse({'success': False, 'error': 'Database name required'})
        
        success, message = db_manager.drop_database(server_id, db_name)
        return JsonResponse({'success': success, 'message': message})


@csrf_exempt
def api_database_info(request, server_id, db_name):
    """Получить информацию о базе данных"""
    if request.method == 'GET':
        info = db_manager.get_database_info(server_id, db_name)
        return JsonResponse(info)


@csrf_exempt
def api_tables(request, server_id, db_name):
    """API для работы с таблицами"""
    if request.method == 'GET':
        tables = db_manager.list_tables(server_id, db_name)
        return JsonResponse({'tables': tables})
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        table_name = data.get('name')
        columns = data.get('columns', [])
        
        if not table_name:
            return JsonResponse({'success': False, 'error': 'Table name required'})
        
        success, message = db_manager.create_table(server_id, db_name, table_name, columns)
        return JsonResponse({'success': success, 'message': message})
    
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        table_name = data.get('name')
        if not table_name:
            return JsonResponse({'success': False, 'error': 'Table name required'})
        
        success, message = db_manager.drop_table(server_id, db_name, table_name)
        return JsonResponse({'success': success, 'message': message})


@csrf_exempt
def api_table_info(request, server_id, db_name, table_name):
    """Получить информацию о таблице"""
    if request.method == 'GET':
        info = db_manager.get_table_info(server_id, db_name, table_name)
        return JsonResponse(info)


@csrf_exempt
def api_rows(request, server_id, db_name, table_name):
    """API для работы со строками таблицы"""
    if request.method == 'GET':
        info = db_manager.get_table_info(server_id, db_name, table_name)
        if 'error' in info:
            return JsonResponse({'success': False, 'error': info['error']})
        return JsonResponse({
            'columns': info['columns'],
            'data': info['data'],
            'row_count': info['row_count']
        })
    
    elif request.method == 'POST':
        data = json.loads(request.body)
        row_data = data.get('data', {})
        
        success, message = db_manager.insert_row(server_id, db_name, table_name, row_data)
        return JsonResponse({'success': success, 'message': message})
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        row_data = data.get('data', {})
        where_clause = data.get('where', '1=1')
        
        success, message = db_manager.update_row(server_id, db_name, table_name, row_data, where_clause)
        return JsonResponse({'success': success, 'message': message})
    
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        where_clause = data.get('where', '1=1')
        
        success, message = db_manager.delete_row(server_id, db_name, table_name, where_clause)
        return JsonResponse({'success': success, 'message': message})


@csrf_exempt
def api_query(request, server_id, db_name):
    """Выполнить произвольный SQL запрос"""
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '')
        
        if not query:
            return JsonResponse({'success': False, 'error': 'Query required'})
        
        success, message, result = db_manager.execute_query(server_id, db_name, query)
        return JsonResponse({
            'success': success,
            'message': message,
            'result': result
        })
