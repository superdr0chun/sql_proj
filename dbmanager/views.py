from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .database import db_manager

def index(request):
    """Main page - database manager interface"""
    if not db_manager.session:
        db_manager.connect()
    
    tables = db_manager.get_tables()
    return render(request, 'dbmanager/index.html', {'tables': tables})

@csrf_exempt
def execute_query(request):
    """Execute raw SQL query"""
    if request.method == 'POST':
        query = request.POST.get('query', '')
        success, message, *rest = db_manager.execute_query(query)
        
        if len(rest) == 2:
            rows, columns = rest
            # Convert rows to list of lists for JSON serialization
            serialized_rows = []
            for row in rows:
                serialized_row = []
                for val in row:
                    serialized_row.append(str(val) if val is not None else None)
                serialized_rows.append(serialized_row)
            
            return JsonResponse({
                'success': success,
                'message': message,
                'columns': columns,
                'rows': serialized_rows
            })
        else:
            return JsonResponse({
                'success': success,
                'message': message,
                'columns': [],
                'rows': []
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
def get_tables(request):
    """Get list of all tables"""
    tables = db_manager.get_tables()
    return JsonResponse({'tables': tables})

@csrf_exempt
def get_table_data(request, table_name):
    """Get all records from a table"""
    success, message, rows, columns = db_manager.get_all_records(table_name)
    
    if success:
        serialized_rows = []
        for row in rows:
            serialized_row = []
            for val in row:
                serialized_row.append(str(val) if val is not None else None)
            serialized_rows.append(serialized_row)
        
        return JsonResponse({
            'success': True,
            'columns': columns,
            'rows': serialized_rows
        })
    else:
        return JsonResponse({'success': False, 'message': message})

@csrf_exempt
def get_table_columns(request, table_name):
    """Get columns for a specific table"""
    columns = db_manager.get_table_columns(table_name)
    return JsonResponse({'columns': columns})

@csrf_exempt
def add_record(request, table_name):
    """Add a new record to a table"""
    if request.method == 'POST':
        data = json.loads(request.body)
        success, message = db_manager.add_record(table_name, data)
        return JsonResponse({'success': success, 'message': message})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
def update_record(request, table_name, record_id, id_column):
    """Update a record in a table"""
    if request.method == 'POST':
        data = json.loads(request.body)
        success, message = db_manager.update_record(table_name, record_id, id_column, data)
        return JsonResponse({'success': success, 'message': message})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
def delete_record(request, table_name, record_id, id_column):
    """Delete a record from a table"""
    if request.method == 'POST':
        success, message = db_manager.delete_record(table_name, record_id, id_column)
        return JsonResponse({'success': success, 'message': message})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
def create_table(request):
    """Create a new table"""
    if request.method == 'POST':
        data = json.loads(request.body)
        table_name = data.get('table_name')
        columns = data.get('columns', [])
        success, message = db_manager.create_table(table_name, columns)
        return JsonResponse({'success': success, 'message': message})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@csrf_exempt
def drop_table(request, table_name):
    """Drop a table"""
    if request.method == 'POST':
        success, message = db_manager.drop_table(table_name)
        return JsonResponse({'success': success, 'message': message})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
