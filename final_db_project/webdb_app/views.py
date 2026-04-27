from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, String, Integer, Float, Boolean, DateTime, Text
from .models import Server, Database

def index(request):
    return render(request, 'webdb_app/index.html')

def get_engine(connection_string):
    """Create SQLAlchemy engine from connection string."""
    if connection_string.startswith('local://'):
        db_name = connection_string.replace('local://', '')
        if not db_name:
            db_name = 'default_local.db'
        return create_engine(f'sqlite:///{db_name}')
    return create_engine(connection_string)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def servers(request):
    if request.method == 'GET':
        servers_list = list(Server.objects.values('id', 'name', 'connection_string', 'server_type'))
        return JsonResponse({'servers': servers_list})
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            connection_string = data.get('connection_string')
            server_type = data.get('server_type', 'postgresql')
            if not name or not connection_string:
                return JsonResponse({'error': 'Name and connection_string are required'}, status=400)
            server, created = Server.objects.get_or_create(
                name=name,
                defaults={'connection_string': connection_string, 'server_type': server_type}
            )
            if not created:
                return JsonResponse({'error': 'Server with this name already exists'}, status=400)
            return JsonResponse({'id': server.id, 'name': server.name, 'message': 'Server created successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def server_detail(request, server_id):
    try:
        server = Server.objects.get(id=server_id)
    except Server.DoesNotExist:
        return JsonResponse({'error': 'Server not found'}, status=404)
    if request.method == 'GET':
        return JsonResponse({
            'id': server.id, 'name': server.name,
            'connection_string': server.connection_string,
            'server_type': server.server_type
        })
    elif request.method == 'DELETE':
        server.delete()
        return JsonResponse({'message': 'Server deleted successfully'})

@csrf_exempt
@require_http_methods(["GET", "POST"])
def databases(request, server_id):
    try:
        server = Server.objects.get(id=server_id)
    except Server.DoesNotExist:
        return JsonResponse({'error': 'Server not found'}, status=404)
    if request.method == 'GET':
        db_list = list(Database.objects.filter(server=server).values('id', 'name'))
        return JsonResponse({'databases': db_list})
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            db_name = data.get('name')
            if not db_name:
                return JsonResponse({'error': 'Database name is required'}, status=400)
            db, created = Database.objects.get_or_create(server=server, name=db_name, defaults={})
            if not created:
                return JsonResponse({'error': 'Database already exists'}, status=400)
            return JsonResponse({'id': db.id, 'name': db.name, 'message': 'Database created successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET", "DELETE"])
def database_detail(request, server_id, db_name):
    try:
        server = Server.objects.get(id=server_id)
        database = Database.objects.get(server=server, name=db_name)
    except (Server.DoesNotExist, Database.DoesNotExist):
        return JsonResponse({'error': 'Database not found'}, status=404)
    if request.method == 'GET':
        return JsonResponse({'id': database.id, 'name': database.name, 'server_name': server.name})
    elif request.method == 'DELETE':
        database.delete()
        return JsonResponse({'message': 'Database deleted successfully'})

@csrf_exempt
@require_http_methods(["GET"])
def tables(request, server_id, db_name):
    try:
        server = Server.objects.get(id=server_id)
        database = Database.objects.get(server=server, name=db_name)
    except (Server.DoesNotExist, Database.DoesNotExist):
        return JsonResponse({'error': 'Database not found'}, status=404)
    try:
        if server.connection_string.startswith('local://'):
            engine = create_engine(f'sqlite:///{server.connection_string.replace("local://", "")}')
        else:
            base = server.connection_string.rsplit('/', 1)[0]
            engine = create_engine(f"{base}/{db_name}")
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        tables_info = []
        for table_name in table_names:
            columns = inspector.get_columns(table_name)
            tables_info.append({'name': table_name, 'columns': len(columns)})
        return JsonResponse({'tables': tables_info})
    except Exception as e:
        return JsonResponse({'error': str(e), 'tables': []}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def create_table(request, server_id, db_name):
    try:
        server = Server.objects.get(id=server_id)
        database = Database.objects.get(server=server, name=db_name)
    except (Server.DoesNotExist, Database.DoesNotExist):
        return JsonResponse({'error': 'Database not found'}, status=404)
    try:
        data = json.loads(request.body)
        table_name = data.get('table_name')
        columns = data.get('columns', [])
        if not table_name or not columns:
            return JsonResponse({'error': 'Table name and columns are required'}, status=400)
        if server.connection_string.startswith('local://'):
            engine = create_engine(f'sqlite:///{server.connection_string.replace("local://", "")}')
        else:
            base = server.connection_string.rsplit('/', 1)[0]
            engine = create_engine(f"{base}/{db_name}")
        metadata = MetaData()
        cols = []
        for col in columns:
            col_type = col.get('type', 'VARCHAR').upper()
            col_name = col.get('name')
            size = col.get('size')
            is_pk = col.get('primary_key', False)
            nullable = col.get('nullable', True)
            if col_type == 'INTEGER':
                sqla_type = Integer()
            elif col_type == 'FLOAT':
                sqla_type = Float()
            elif col_type == 'BOOLEAN':
                sqla_type = Boolean()
            elif col_type == 'DATETIME':
                sqla_type = DateTime()
            elif col_type == 'TEXT':
                sqla_type = Text()
            else:
                sqla_type = String(length=int(size) if size else 255)
            column_obj = Column(col_name, sqla_type, primary_key=is_pk, nullable=nullable)
            cols.append(column_obj)
        table = Table(table_name, metadata, *cols)
        metadata.create_all(engine)
        return JsonResponse({'message': f'Table {table_name} created successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_table(request, server_id, db_name, table_name):
    try:
        server = Server.objects.get(id=server_id)
        database = Database.objects.get(server=server, name=db_name)
    except (Server.DoesNotExist, Database.DoesNotExist):
        return JsonResponse({'error': 'Database not found'}, status=404)
    try:
        if server.connection_string.startswith('local://'):
            engine = create_engine(f'sqlite:///{server.connection_string.replace("local://", "")}')
        else:
            base = server.connection_string.rsplit('/', 1)[0]
            engine = create_engine(f"{base}/{db_name}")
        with engine.connect() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            conn.commit()
        return JsonResponse({'message': f'Table {table_name} deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def table_data(request, server_id, db_name, table_name):
    try:
        server = Server.objects.get(id=server_id)
        database = Database.objects.get(server=server, name=db_name)
    except (Server.DoesNotExist, Database.DoesNotExist):
        return JsonResponse({'error': 'Database not found'}, status=404)
    try:
        if server.connection_string.startswith('local://'):
            engine = create_engine(f'sqlite:///{server.connection_string.replace("local://", "")}')
        else:
            base = server.connection_string.rsplit('/', 1)[0]
            engine = create_engine(f"{base}/{db_name}")
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 100"))
            rows = [dict(row._mapping) for row in result]
        columns_info = []
        for col in columns:
            columns_info.append({
                'name': col['name'], 'type': str(col['type']),
                'nullable': col.get('nullable', True),
                'primary_key': col.get('primary_key', False)
            })
        return JsonResponse({'columns': columns_info, 'data': rows, 'count': len(rows)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def insert_row(request, server_id, db_name, table_name):
    try:
        server = Server.objects.get(id=server_id)
        database = Database.objects.get(server=server, name=db_name)
    except (Server.DoesNotExist, Database.DoesNotExist):
        return JsonResponse({'error': 'Database not found'}, status=404)
    try:
        data = json.loads(request.body)
        if server.connection_string.startswith('local://'):
            engine = create_engine(f'sqlite:///{server.connection_string.replace("local://", "")}')
        else:
            base = server.connection_string.rsplit('/', 1)[0]
            engine = create_engine(f"{base}/{db_name}")
        columns = list(data.keys())
        placeholders = ', '.join([':' + col for col in columns])
        columns_str = ', '.join(columns)
        with engine.connect() as conn:
            conn.execute(text(f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"), data)
            conn.commit()
        return JsonResponse({'message': 'Row inserted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def execute_sql(request):
    try:
        data = json.loads(request.body)
        server_id = data.get('server_id')
        db_name = data.get('database')
        sql_query = data.get('query')
        if not server_id or not db_name or not sql_query:
            return JsonResponse({'error': 'Server ID, database, and query are required'}, status=400)
        server = Server.objects.get(id=server_id)
        if server.connection_string.startswith('local://'):
            engine = create_engine(f'sqlite:///{server.connection_string.replace("local://", "")}')
        else:
            base = server.connection_string.rsplit('/', 1)[0]
            engine = create_engine(f"{base}/{db_name}")
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            conn.commit()
            if sql_query.strip().upper().startswith('SELECT'):
                rows = [dict(row._mapping) for row in result]
                return JsonResponse({'success': True, 'data': rows, 'count': len(rows)})
            else:
                return JsonResponse({'success': True, 'message': f'{result.rowcount} rows affected'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
