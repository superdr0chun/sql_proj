from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError


class DatabaseManager:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.engine = None

    def connect(self):
        try:
            self.engine = create_engine(self.connection_string)
            return True, "Connected successfully"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def execute_query(self, query):
        if not self.engine:
            return False, "Not connected", [], []
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                if query.strip().upper().startswith(('SELECT', 'SHOW', 'EXPLAIN', 'DESCRIBE')):
                    columns = [col for col in result.keys()]
                    rows = [list(row) for row in result.fetchall()]
                    return True, f"Query executed. {len(rows)} rows returned.", columns, rows
                else:
                    conn.commit()
                    return True, f"Query executed. Rows affected: {result.rowcount}", [], []
        except Exception as e:
            return False, str(e), [], []

    def get_databases(self):
        if not self.engine:
            return []
        
        try:
            inspector = inspect(self.engine)
            return inspector.get_schema_names()
        except Exception:
            return []

    def get_tables(self, database=None):
        if not self.engine:
            return []
        
        try:
            inspector = inspect(self.engine)
            if database:
                with self.engine.connect() as conn:
                    conn.execute(text(f"USE {database}")) if self.engine.dialect.name == 'mysql' else None
            return inspector.get_table_names()
        except Exception:
            return []

    def get_table_info(self, table_name, schema=None):
        if not self.engine:
            return None
        
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name, schema=schema)
            primary_keys = inspector.get_primary_keys(table_name, schema=schema)
            
            table_data = {
                'columns': [],
                'primary_keys': primary_keys
            }
            
            for col in columns:
                table_data['columns'].append({
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col.get('nullable', True),
                    'default': col.get('default'),
                    'is_primary': col['name'] in primary_keys
                })
            
            return table_data
        except Exception as e:
            return None

    def get_table_data(self, table_name, limit=100, schema=None):
        if not self.engine:
            return False, "Not connected", [], []
        
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT * FROM {table_name} LIMIT :limit")
                result = conn.execute(query, {"limit": limit})
                columns = [col for col in result.keys()]
                rows = [list(row) for row in result.fetchall()]
                return True, f"Retrieved {len(rows)} rows", columns, rows
        except Exception as e:
            return False, str(e), [], []

    def create_database(self, db_name):
        if not self.engine:
            return False, "Not connected"
        
        try:
            with self.engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(f"CREATE DATABASE {db_name}")
                )
                return True, f"Database {db_name} created"
        except Exception as e:
            return False, str(e)

    def drop_database(self, db_name):
        if not self.engine:
            return False, "Not connected"
        
        try:
            with self.engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(f"DROP DATABASE IF EXISTS {db_name}")
                )
                return True, f"Database {db_name} dropped"
        except Exception as e:
            return False, str(e)

    def create_table(self, table_name, columns, schema=None):
        if not self.engine:
            return False, "Not connected"
        
        try:
            column_defs = []
            for col in columns:
                col_def = f"{col['name']} {col['type']}"
                if col.get('size') and 'VARCHAR' in col['type'].upper():
                    col_def += f"({col['size']})"
                if col.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if not col.get('nullable', True):
                    col_def += " NOT NULL"
                if col.get('default'):
                    col_def += f" DEFAULT {col['default']}"
                column_defs.append(col_def)
            
            query = f"CREATE TABLE {table_name} (" + ", ".join(column_defs) + ")"
            
            with self.engine.connect() as conn:
                conn.execute(text(query))
                conn.commit()
                return True, f"Table {table_name} created"
        except Exception as e:
            return False, str(e)

    def drop_table(self, table_name, schema=None):
        if not self.engine:
            return False, "Not connected"
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                conn.commit()
                return True, f"Table {table_name} dropped"
        except Exception as e:
            return False, str(e)

    def insert_row(self, table_name, data):
        if not self.engine:
            return False, "Not connected"
        
        try:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ', '.join([':' + col for col in columns])
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            with self.engine.connect() as conn:
                conn.execute(text(query), data)
                conn.commit()
                return True, "Row inserted"
        except Exception as e:
            return False, str(e)

    def update_row(self, table_name, data, where_clause):
        if not self.engine:
            return False, "Not connected"
        
        try:
            set_clause = ', '.join([f"{col} = :{col}" for col in data.keys()])
            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query), data)
                conn.commit()
                return True, f"Rows updated: {result.rowcount}"
        except Exception as e:
            return False, str(e)

    def delete_row(self, table_name, where_clause):
        if not self.engine:
            return False, "Not connected"
        
        try:
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                conn.commit()
                return True, f"Rows deleted: {result.rowcount}"
        except Exception as e:
            return False, str(e)
