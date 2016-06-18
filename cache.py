from flask import g
import datetime
import sqlite3
from contextlib import closing

CACHE_DB = 'cache.db'

def get_db():
    db = getattr(g, '_cache_db', None)
    if db is None:
        db = g._database = sqlite3.connect(CACHE_DB)
        db.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY, value TEXT, expire_at INTEGER)''')

    return db

def to_epoch(t):
    diff = t - datetime.datetime(1970, 1, 1)
    return diff.total_seconds()


def set(k, v, timeout):
    db = get_db()
    expire_at = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    with closing(db.cursor()) as c:
        c.execute('INSERT OR REPLACE INTO cache (key, value, expire_at) VALUES (?, ?, ?)',
            (k, v, to_epoch(expire_at)))
        db.commit()


def get(k):
    db = get_db()
    with closing(db.cursor()) as c:
        c.execute('SELECT * FROM cache WHERE key = ?', (k,))
        row = c.fetchone()
        if row is None:
            return None

        _, v, expire_at = row
        if expire_at < to_epoch(datetime.datetime.now()):
            # key expired
            c.execute('DELETE FROM cache WHERE key = ?', (k,))
            db.commit()
            return None
        
    return v
