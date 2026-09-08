"""PostgreSQL/MySQL 占位符转换测试。"""

from chem_agent.auth.db_backends.mysql_backend import MySQLAuthDB
from chem_agent.auth.db_backends.postgres_backend import PostgresAuthDB
from chem_agent.auth.db_backends.sqlite_backend import SQLiteAuthDB


def test_postgres_formats_qmark_to_percent_s():
    backend = PostgresAuthDB.__new__(PostgresAuthDB)
    sql = "SELECT * FROM formula_versions WHERE formula_code = ? AND version_number = ?"
    assert backend.format_sql(sql) == sql.replace("?", "%s")


def test_mysql_formats_qmark_to_percent_s():
    backend = MySQLAuthDB.__new__(MySQLAuthDB)
    sql = "UPDATE system_configs SET value = ? WHERE key = ?"
    assert backend.format_sql(sql) == sql.replace("?", "%s")


def test_sqlite_keeps_qmark():
    backend = SQLiteAuthDB(db_path=":memory:")
    sql = "SELECT * FROM users WHERE id = ?"
    assert backend.format_sql(sql) == sql
