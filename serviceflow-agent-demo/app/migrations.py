from sqlalchemy import text

from app.database import engine


TABLE_COLUMNS = {
    "conversations": {
        "assigned_agent_id": "TEXT",
        "handoff_status": "TEXT DEFAULT 'NONE'",
    },
    "tickets": {
        "assigned_agent_id": "TEXT",
        "resolution": "TEXT",
        "updated_at": "DATETIME",
    },
    "chat_logs": {
        "sender": "TEXT DEFAULT 'agent'",
        "trace_id": "TEXT",
    },
    "admin_users": {
        "password_hash": "TEXT",
    },
}


def ensure_schema_updates() -> None:
    with engine.begin() as connection:
        for table_name, columns in TABLE_COLUMNS.items():
            existing = {
                row[1]
                for row in connection.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }
            for column_name, ddl in columns.items():
                if column_name not in existing:
                    # SQLite 演示库没有 Alembic，这里只做向后兼容的追加列迁移。
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl}"))
