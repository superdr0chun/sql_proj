import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

# In-memory storage for server connections
SERVERS = {}
SERVER_COUNTER = 0

def get_engine(server_id):
    if server_id not in SERVERS:
        return None
    return SERVERS[server_id]['engine']

@csrf_exempt
def index(request):
    return render(request, 'mydb/index.html')

@csrf_exempt
def add_server(request):
    global SERVER_COUNTER
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name', 'Server')
        conn_str = data.get('connection_string', '')
        
        if not conn_str:
            import os
            db_file = f"server_{SERVER_COUNTER}.sqlite3"
            conn_str = f"sqlite:///{db_file}"
            display_name = f"{name} (Local SQLite)"
        else:
            display_name = name

        try:
            engine = create_engine(conn_str)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            SERVER_COUNTER += 1
            server_id = f"srv_{SERVER_COUNTER}"
            SERVERS[server_id] = {
                'name': display_name,
                'connection_string': conn_str,
                'engine': engine
            }
            return JsonResponse({'success': True, 'id': server_id, 'name': display_name})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def get_servers(request):
    servers = []
    for sid, data in SERVERS.items():
        engines = get_engine(sid)
        if engines:
            url_obj = make_url(data['connection_string'])
            db_name = url_obj.database or "default"
            
            servers.append({
                'id': sid,
                'name': data['name'],
                'db_name': db_name
            })
    return JsonResponse({'servers': servers})

@csrf_exempt
def get_tables(request, server_id):
    engine = get_engine(server_id)
    if not engine:
        return JsonResponse({'tables': []})
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return JsonResponse({'tables': tables})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def get_table_info(request, server_id, table_name):
    engine = get_engine(server_id)
    if not engine:
        return JsonResponse({'error': 'Server not found'}, status=404)
    
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        with engine.connect() as conn:
            result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT 100'))
            rows = [dict(row._mapping) for row in result]
        
        return JsonResponse({
            'columns': columns,
            'data': rows
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def execute_sql(request, server_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    
    engine = get_engine(server_id)
    if not engine:
        return JsonResponse({'error': 'Server not found'}, status=404)

    data = json.loads(request.body)
    query = data.get('sql', '')
    
    try:
        with engine.connect() as conn:
            res = conn.execute(text(query))
            conn.commit()
            
            if query.strip().lower().startswith('select'):
                rows = [dict(row._mapping) for row in res]
                return JsonResponse({'success': True, 'data': rows, 'message': 'Query executed'})
            else:
                return JsonResponse({'success': True, 'message': 'Query executed successfully', 'rows_affected': res.rowcount})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
def create_table(request, server_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    
    engine = get_engine(server_id)
    if not engine:
        return JsonResponse({'error': 'Server not found'}, status=404)

    data = json.loads(request.body)
    table_name = data.get('table_name')
    columns_def = data.get('columns', [])
    
    if not table_name or not columns_def:
        return JsonResponse({'error': 'Name and columns required'}, status=400)

    try:
        metadata = MetaData()
        cols = []
        for col in columns_def:
            col_type = col['type']
            args = []
            kwargs = {}
            
            if col.get('size'):
                args.append(int(col['size']))
            
            if col.get('pk'):
                kwargs['primary_key'] = True
            
            if not col.get('nullable', True):
                kwargs['nullable'] = False

            type_map = {
                'INTEGER': Integer,
                'VARCHAR': String,
                'TEXT': String,
                'FLOAT': Float,
                'BOOLEAN': Boolean,
                'DATETIME': DateTime
            }
            
            sqla_type = type_map.get(col_type.upper(), String)
            cols.append(Column(col['name'], sqla_type(*args), **kwargs))

        new_table = Table(table_name, metadata, *cols)
        metadata.create_all(engine)
        
        return JsonResponse({'success': True, 'message': f'Table {table_name} created'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
def delete_table(request, server_id, table_name):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    engine = get_engine(server_id)
    if not engine:
        return JsonResponse({'error': 'Server not found'}, status=404)

    try:
        with engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.commit()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def insert_row(request, server_id, table_name):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=400)
    
    engine = get_engine(server_id)
    if not engine:
        return JsonResponse({'error': 'Server not found'}, status=404)

    data = json.loads(request.body)
    row_data = data.get('data', {})
    
    if not row_data:
        return JsonResponse({'error': 'No data provided'}, status=400)

    try:
        columns = ', '.join([f'"{k}"' for k in row_data.keys()])
        placeholders = ', '.join([f':{k}' for k in row_data.keys()])
        query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
        
        with engine.connect() as conn:
            conn.execute(text(query), row_data)
            conn.commit()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def delete_server(request, server_id):
    if request.method == 'DELETE':
        if server_id in SERVERS:
            del SERVERS[server_id]
            return JsonResponse({'success': True})
    return JsonResponse({'error': 'Not found'}, status=404)
