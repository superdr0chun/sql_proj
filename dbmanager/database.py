from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from django.conf import settings

class DatabaseManager:
    def __init__(self, connection_string=None):
        if connection_string is None:
            # Use SQLite by default for demo
            db_path = settings.BASE_DIR / 'demo_database.sqlite'
            self.connection_string = f'sqlite:///{db_path}'
        else:
            self.connection_string = connection_string
        
        self.engine = None
        self.Session = None
        self.session = None
    
    def connect(self):
        """Connect to the database"""
        try:
            self.engine = create_engine(self.connection_string)
            self.Session = sessionmaker(bind=self.engine)
            self.session = self.Session()
            return True, "Connected successfully"
        except Exception as e:
            return False, str(e)
    
    def disconnect(self):
        """Disconnect from the database"""
        if self.session:
            self.session.close()
        self.engine = None
        self.Session = None
        self.session = None
    
    def get_tables(self):
        """Get list of all tables"""
        if not self.engine:
            return []
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_table_columns(self, table_name):
        """Get columns for a specific table"""
        if not self.engine:
            return []
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        return [col['name'] for col in columns]
    
    def execute_query(self, query):
        """Execute a raw SQL query"""
        if not self.session:
            return False, "Not connected", []
        
        try:
            result = self.session.execute(text(query))
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                rows = result.fetchall()
                columns = list(result.keys()) if result.keys() else []
                return True, f"Query executed successfully. {len(rows)} rows returned.", rows, columns
            else:
                self.session.commit()
                return True, f"Query executed successfully. {result.rowcount} rows affected.", [], []
        except Exception as e:
            self.session.rollback()
            return False, str(e), [], []
    
    def get_all_records(self, table_name):
        """Get all records from a table"""
        query = f'SELECT * FROM "{table_name}"'
        return self.execute_query(query)
    
    def add_record(self, table_name, data):
        """Add a new record to a table"""
        if not self.session:
            return False, "Not connected"
        
        try:
            columns = ', '.join([f'"{k}"' for k in data.keys()])
            placeholders = ', '.join([':' + k for k in data.keys()])
            values = {k: v for k, v in data.items()}
            
            query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
            self.session.execute(text(query), values)
            self.session.commit()
            return True, "Record added successfully"
        except Exception as e:
            self.session.rollback()
            return False, str(e)
    
    def update_record(self, table_name, record_id, id_column, data):
        """Update a record in a table"""
        if not self.session:
            return False, "Not connected"
        
        try:
            set_clause = ', '.join([f'"{k}" = :{k}' for k in data.keys()])
            values = {k: v for k, v in data.items()}
            values[id_column] = record_id
            
            query = f'UPDATE "{table_name}" SET {set_clause} WHERE "{id_column}" = :{id_column}'
            result = self.session.execute(text(query), values)
            self.session.commit()
            return True, f"Record updated. {result.rowcount} rows affected."
        except Exception as e:
            self.session.rollback()
            return False, str(e)
    
    def delete_record(self, table_name, record_id, id_column):
        """Delete a record from a table"""
        if not self.session:
            return False, "Not connected"
        
        try:
            query = f'DELETE FROM "{table_name}" WHERE "{id_column}" = :id'
            result = self.session.execute(text(query), {'id': record_id})
            self.session.commit()
            return True, f"Record deleted. {result.rowcount} rows affected."
        except Exception as e:
            self.session.rollback()
            return False, str(e)
    
    def create_table(self, table_name, columns):
        """Create a new table"""
        if not self.session:
            return False, "Not connected"
        
        try:
            column_defs = []
            for col in columns:
                col_def = f'"{col["name"]}" {col["type"]}'
                if col.get('primary_key'):
                    col_def += ' PRIMARY KEY'
                if col.get('auto_increment'):
                    if 'sqlite' in self.connection_string:
                        col_def += ' AUTOINCREMENT'
                    else:
                        col_def += ' AUTO_INCREMENT'
                if col.get('not_null'):
                    col_def += ' NOT NULL'
                column_defs.append(col_def)
            
            query = f'CREATE TABLE "{table_name}" (' + ', '.join(column_defs) + ')'
            self.session.execute(text(query))
            self.session.commit()
            return True, "Table created successfully"
        except Exception as e:
            self.session.rollback()
            return False, str(e)
    
    def drop_table(self, table_name):
        """Drop a table"""
        if not self.session:
            return False, "Not connected"
        
        try:
            query = f'DROP TABLE "{table_name}"'
            self.session.execute(text(query))
            self.session.commit()
            return True, "Table dropped successfully"
        except Exception as e:
            self.session.rollback()
            return False, str(e)


# Global instance
db_manager = DatabaseManager()
