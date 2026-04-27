# WebDB Manager - SQLAlchemy Admin

Веб-СУБД в стиле pgAdmin4 на Django + SQLAlchemy

## Возможности

- 🗄️ **Древовидная структура**: Сервера → Базы данных → Таблицы
- ➕ **Создание серверов**: Локальные (SQLite) и PostgreSQL
- 📊 **Управление БД**: Создание, удаление баз данных
- 📋 **Управление таблицами**: Создание с детальным указанием колонок (тип, размер, PK, nullable)
- 👁 **Просмотр данных**: Отображение структуры и содержимого таблиц
- ✏️ **CRUD операции**: Добавление, редактирование, удаление записей
- 💻 **SQL редактор**: Выполнение произвольных SQL запросов (Ctrl+Enter)
- 🖱️ **Контекстное меню**: Правый клик по элементам дерева

## Установка

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Использование

1. Откройте http://localhost:8000
2. Нажмите "+ Server" для добавления сервера
3. Выберите тип подключения:
   - **Local (SQLite)**: Укажите путь к файлу БД
   - **PostgreSQL**: Введите host, port, username, password, database
4. Раскройте сервер в дереве для просмотра БД
5. Правый клик по элементам для операций

## Структура проекта

```
webdb_project/
├── manage.py
├── db.sqlite3              # Django DB для хранения серверов
├── requirements.txt
├── webdb_project/          # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── webdb_app/              # Приложение
    ├── models.py           # Модели Server, SavedQuery
    ├── views.py            # API endpoints
    ├── database.py         # DatabaseManager на SQLAlchemy
    ├── urls.py             # URL маршруты
    └── templates/
        └── webdb_app/
            └── index.html  # Веб-интерфейс
```

## Требования

- Python 3.8+
- Django 4.2+
- SQLAlchemy 2.0+
- psycopg2-binary (для PostgreSQL)
