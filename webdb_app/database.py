"""
Менеджер баз данных на SQLAlchemy.
Управляет серверами, базами данных и таблицами через SQLAlchemy.
"""
from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import json

Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        self.servers = {}  # server_id -> connection_string
        self.engines = {}  # server_id -> engine
        self._load_servers()
    
    def _load_servers(self):
        """Загружает сервера из Django settings или использует дефолтные"""
        # По умолчанию добавляем локальный PostgreSQL
        self.add_server('default', 'postgresql://postgres:postgres@localhost:5432/postgres')
    
    def add_server(self, server_id, connection_string):
        """Добавляет сервер подключения"""
        self.servers[server_id] = connection_string
        try:
            engine = create_engine(connection_string, poolclass=NullPool)
            self.engines[server_id] = engine
            return True
        except Exception as e:
            return False
    
    def remove_server(self, server_id):
        """Удаляет сервер"""
        if server_id in self.servers:
            del self.servers[server_id]
        if server_id in self.engines:
            del self.engines[server_id]
    
    def get_server_info(self, server_id):
        """Получает информацию о сервере"""
        if server_id not in self.servers:
            return None
        return {
            'id': server_id,
            'connection_string': self.servers[server_id],
            'status': 'connected' if server_id in self.engines else 'disconnected'
        }
    
    def list_servers(self):
        """Возвращает список всех серверов"""
        result = []
        for sid in self.servers.keys():
            status = 'connected'
            # Проверяем подключение
            try:
                if sid in self.engines:
                    with self.engines[sid].connect() as conn:
                        conn.execute(text("SELECT 1"))
            except:
                status = 'disconnected'
            result.append({'id': sid, 'status': status})
        return result
    
    def get_engine(self, server_id):
        """Получает движок для сервера"""
        return self.engines.get(server_id)
    
    def get_session(self, server_id, database=None):
        """Создает сессию для работы с БД"""
        if server_id not in self.engines:
            return None
        
        engine = self.engines[server_id]
        
        # Если указана конкретная база данных, создаем новый движок
        if database:
            # Получаем базовый URL без имени БД
            url = str(engine.url)
            # Заменяем базу данных в URL
            from sqlalchemy.engine import make_url
            parsed_url = make_url(url)
            new_url = parsed_url.set(database=database)
            engine = create_engine(new_url, poolclass=NullPool)
        
        Session = sessionmaker(bind=engine)
        return Session()
    
    def list_databases(self, server_id):
        """Получает список баз данных на сервере"""
        if server_id not in self.engines:
            return []
        
        try:
            engine = self.engines[server_id]
            # Для PostgreSQL
            with engine.connect() as conn:
                result = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false"))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            return []
    
    def create_database(self, server_id, db_name):
        """Создает базу данных"""
        if server_id not in self.engines:
            return False, "Server not found"
        
        try:
            engine = self.engines[server_id]
            # Подключаемся к postgres для создания БД
            with engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(f'CREATE DATABASE "{db_name}"')
                )
            return True, "Database created"
        except Exception as e:
            return False, str(e)
    
    def drop_database(self, server_id, db_name):
        """Удаляет базу данных"""
        if server_id not in self.engines:
            return False, "Server not found"
        
        try:
            engine = self.engines[server_id]
            with engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(f'DROP DATABASE IF EXISTS "{db_name}"')
                )
            return True, "Database dropped"
        except Exception as e:
            return False, str(e)
    
    def get_database_info(self, server_id, db_name):
        """Получает информацию о базе данных"""
        if server_id not in self.engines:
            return None
        
        try:
            session = self.get_session(server_id, db_name)
            inspector = inspect(session.bind)
            
            tables = inspector.get_table_names()
            
            return {
                'name': db_name,
                'tables_count': len(tables),
                'tables': tables
            }
        except Exception as e:
            return {'error': str(e)}
    
    def list_tables(self, server_id, db_name):
        """Получает список таблиц в базе данных"""
        if server_id not in self.engines:
            return []
        
        try:
            session = self.get_session(server_id, db_name)
            inspector = inspect(session.bind)
            return inspector.get_table_names()
        except Exception as e:
            return []
    
    def get_table_info(self, server_id, db_name, table_name):
        """Получает подробную информацию о таблице"""
        if server_id not in self.engines:
            return None
        
        try:
            session = self.get_session(server_id, db_name)
            inspector = inspect(session.bind)
            
            columns = inspector.get_columns(table_name)
            primary_keys = inspector.get_pk_constraint(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            indexes = inspector.get_indexes(table_name)
            
            # Получаем данные из таблицы
            result = session.execute(text(f'SELECT * FROM "{table_name}" LIMIT 100'))
            rows = [dict(row._mapping) for row in result.fetchall()]
            
            return {
                'name': table_name,
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'indexes': indexes,
                'data': rows,
                'row_count': len(rows)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def create_table(self, server_id, db_name, table_name, columns):
        """Создает таблицу с указанными колонками"""
        if server_id not in self.engines:
            return False, "Server not found"
        
        try:
            session = self.get_session(server_id, db_name)
            
            # Создаем колонки
            sqlalchemy_columns = []
            for col in columns:
                col_type = col.get('type', 'VARCHAR').upper()
                col_name = col.get('name', 'column')
                is_primary = col.get('primary_key', False)
                is_nullable = col.get('nullable', True)
                
                # Маппинг типов
                type_map = {
                    'INTEGER': Integer,
                    'INT': Integer,
                    'VARCHAR': String,
                    'STRING': String,
                    'TEXT': Text,
                    'FLOAT': Float,
                    'BOOLEAN': Boolean,
                    'BOOL': Boolean,
                    'DATETIME': DateTime,
                    'TIMESTAMP': DateTime,
                }
                
                sa_type = type_map.get(col_type, String)
                if col_type in ['VARCHAR', 'STRING']:
                    size = col.get('size', 255)
                    column = Column(col_name, sa_type(length=size), nullable=is_nullable, primary_key=is_primary)
                else:
                    column = Column(col_name, sa_type, nullable=is_nullable, primary_key=is_primary)
                
                sqlalchemy_columns.append(column)
            
            # Создаем таблицу
            metadata = MetaData()
            table = Table(table_name, metadata, *sqlalchemy_columns)
            metadata.create_all(session.bind)
            session.commit()
            
            return True, "Table created"
        except Exception as e:
            return False, str(e)
    
    def drop_table(self, server_id, db_name, table_name):
        """Удаляет таблицу"""
        if server_id not in self.engines:
            return False, "Server not found"
        
        try:
            session = self.get_session(server_id, db_name)
            session.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            session.commit()
            return True, "Table dropped"
        except Exception as e:
            return False, str(e)
    
    def insert_row(self, server_id, db_name, table_name, data):
        """Добавляет строку в таблицу"""
        if server_id not in self.engines:
            return False, "Server not found"
        
        try:
            session = self.get_session(server_id, db_name)
            
            columns = ', '.join([f'"{k}"' for k in data.keys()])
            placeholders = ', '.join([f':{k}' for k in data.keys()])
            query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders})'
            
            session.execute(text(query), data)
            session.commit()
            return True, "Row inserted"
        except Exception as e:
            return False, str(e)
    
    def update_row(self, server_id, db_name, table_name, data, where_clause):
        """Обновляет строки в таблице"""
        if server_id not in self.engines:
            return False, "Server not found"
        
        try:
            session = self.get_session(server_id, db_name)
            
            set_clause = ', '.join([f'"{k}" = :{k}' for k in data.keys()])
            query = f'UPDATE "{table_name}" SET {set_clause} WHERE {where_clause}'
            
            params = {**data}
            session.execute(text(query), params)
            session.commit()
            return True, "Rows updated"
        except Exception as e:
            return False, str(e)
    
    def delete_row(self, server_id, db_name, table_name, where_clause):
        """Удаляет строки из таблицы"""
        if server_id not in self.engines:
            return False, "Server not found"
        
        try:
            session = self.get_session(server_id, db_name)
            query = f'DELETE FROM "{table_name}" WHERE {where_clause}'
            session.execute(text(query))
            session.commit()
            return True, "Rows deleted"
        except Exception as e:
            return False, str(e)
    
    def execute_query(self, server_id, db_name, query):
        """Выполняет произвольный SQL запрос"""
        if server_id not in self.engines:
            return False, "Server not found", []
        
        try:
            session = self.get_session(server_id, db_name)
            result = session.execute(text(query))
            
            # Проверяем тип запроса
            if query.strip().upper().startswith('SELECT'):
                rows = [dict(row._mapping) for row in result.fetchall()]
                columns = list(rows[0].keys()) if rows else []
                return True, "Query executed", {'data': rows, 'columns': columns}
            else:
                session.commit()
                return True, "Query executed", {'affected_rows': result.rowcount}
        except Exception as e:
            return False, str(e), []


# Глобальный экземпляр
db_manager = DatabaseManager()
