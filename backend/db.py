from flask import current_app, g

from database.db import connect

def get_db():
    if"db" not in g:
        g.db = connect(current_app.config["DB_PATH"], read_only=True)
    return g.db


def close_db(error= None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()