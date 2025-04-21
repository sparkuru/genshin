# -*- coding: utf-8 -*-

import sqlite3
import os

db_path = "2tencent_data.db"
sql_path = "sql.sql"


def execute_sql_from_file(db_file, sql_file):
    if not os.path.exists(db_file):
        print(f"db_file not found: {db_file}")
        return

    if not os.path.exists(sql_file):
        print(f"sql file not found: {sql_file}")
        return

    try:
        connection = sqlite3.connect(db_file)
        cursor = connection.cursor()
        print(f"connecting to {db_file}")

        with open(sql_file, "r", encoding="utf-8") as file:
            sql_script = file.read()

        sql_statements = sql_script.strip().split(";")
        for statement in sql_statements:
            if statement.strip():
                print(f"\nrun sql: {statement.strip()}")
                cursor.execute(statement)

                if statement.strip().lower().startswith("select"):
                    rows = cursor.fetchall()
                    for row in rows:
                        print(row)

        connection.commit()
        print("\nsql done")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"error: {e}")
    finally:
        if connection:
            connection.close()
            print("connection closed")


if __name__ == "__main__":
    execute_sql_from_file(db_path, sql_path)
