from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
import json

from .database import DatabaseManager
from .models import Server


def index(request):
    return render(request, 'webdb_app/index.html')


# Cache for active connections
connections = {}


def get_connection(server_id):
    if server_id in connections:
        return connections[server_id]
    
    try:
        server = Server.objects.get(id=server_id)
        
        # Build connection string based on database type
        if server.host == 'local':
            # Local SQLite file-based database
            conn_string = f"sqlite:///{server.database}"
        else:
            # PostgreSQL connection
            password_part = f":{server.password}" if server.password else ""
            conn_string = f"postgresql://{server.username}{password_part}@{server.host}:{server.port}/{server.database}"
        
        db_manager = DatabaseManager(conn_string)
        success, message = db_manager.connect()
        
        if success:
            connections[server_id] = db_manager
            return db_manager
        else:
            return None
    except Server.DoesNotExist:
        return None


@csrf_exempt
@require_http_methods(["POST"])
def add_server(request):
    try:
        data = json.loads(request.body)
        name = data.get('name')
        host = data.get('host', 'localhost')
        port = int(data.get('port', 5432))
        username = data.get('username', 'postgres')
        password = data.get('password', '')
        database = data.get('database', 'postgres')
        
        if not name:
            return JsonResponse({'success': False, 'error': 'Server name is required'})
        
        server, created = Server.objects.get_or_create(
            name=name,
            defaults={
                'host': host,
                'port': port,
                'username': username,
                'password': password,
                'database': database
            }
        )
        
        if not created:
            server.host = host
            server.port = port
            server.username = username
            server.password = password
            server.database = database
            server.save()
        
        return JsonResponse({
            'success': True,
            'server': {
                'id': server.id,
                'name': server.name,
                'host': server.host,
                'port': server.port,
                'database': server.database
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def delete_server(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        
        server = Server.objects.get(id=server_id)
        server.delete()
        
        if server_id in connections:
            connections[server_id].disconnect()
            del connections[server_id]
        
        return JsonResponse({'success': True})
    except Server.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Server not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["GET"])
def get_servers(request):
    servers = Server.objects.all()
    return JsonResponse({
        'success': True,
        'servers': [
            {
                'id': s.id,
                'name': s.name,
                'host': s.host,
                'port': s.port,
                'database': s.database
            }
            for s in servers
        ]
    })


@csrf_exempt
@require_http_methods(["POST"])
def get_databases(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        databases = db_manager.get_databases()
        return JsonResponse({'success': True, 'databases': databases})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def create_database(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        db_name = data.get('name')
        
        if not db_name:
            return JsonResponse({'success': False, 'error': 'Database name is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message = db_manager.create_database(db_name)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def drop_database(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        db_name = data.get('name')
        
        if not db_name:
            return JsonResponse({'success': False, 'error': 'Database name is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message = db_manager.drop_database(db_name)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def get_tables(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        database = data.get('database')
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        tables = db_manager.get_tables(database)
        return JsonResponse({'success': True, 'tables': tables})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def create_table(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        table_name = data.get('table_name')
        columns = data.get('columns', [])
        
        if not table_name:
            return JsonResponse({'success': False, 'error': 'Table name is required'})
        
        if not columns:
            return JsonResponse({'success': False, 'error': 'At least one column is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message = db_manager.create_table(table_name, columns)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def drop_table(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        table_name = data.get('table_name')
        
        if not table_name:
            return JsonResponse({'success': False, 'error': 'Table name is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message = db_manager.drop_table(table_name)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def get_table_info(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        table_name = data.get('table_name')
        
        if not table_name:
            return JsonResponse({'success': False, 'error': 'Table name is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        info = db_manager.get_table_info(table_name)
        if info:
            return JsonResponse({'success': True, 'info': info})
        else:
            return JsonResponse({'success': False, 'error': 'Failed to get table info'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def get_table_data(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        table_name = data.get('table_name')
        limit = int(data.get('limit', 100))
        
        if not table_name:
            return JsonResponse({'success': False, 'error': 'Table name is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message, columns, rows = db_manager.get_table_data(table_name, limit)
        return JsonResponse({
            'success': success,
            'message': message,
            'columns': columns,
            'data': rows
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def execute_query(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        query = data.get('query')
        
        if not query:
            return JsonResponse({'success': False, 'error': 'Query is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message, columns, rows = db_manager.execute_query(query)
        return JsonResponse({
            'success': success,
            'message': message,
            'columns': columns,
            'data': rows
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def insert_row(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        table_name = data.get('table_name')
        row_data = data.get('data', {})
        
        if not table_name or not row_data:
            return JsonResponse({'success': False, 'error': 'Table name and data are required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message = db_manager.insert_row(table_name, row_data)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def update_row(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        table_name = data.get('table_name')
        row_data = data.get('data', {})
        where_clause = data.get('where', '1=1')
        
        if not table_name or not row_data:
            return JsonResponse({'success': False, 'error': 'Table name and data are required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message = db_manager.update_row(table_name, row_data, where_clause)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def delete_row(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        table_name = data.get('table_name')
        where_clause = data.get('where', '1=1')
        
        if not table_name:
            return JsonResponse({'success': False, 'error': 'Table name is required'})
        
        db_manager = get_connection(server_id)
        if not db_manager:
            return JsonResponse({'success': False, 'error': 'Failed to connect to server'})
        
        success, message = db_manager.delete_row(table_name, where_clause)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
