"""
Database connection + query helpers.
Uses Supabase Postgres via psycopg2. Connection string comes from
st.secrets["postgres_url"] (set in Streamlit Cloud Settings -> Secrets,
or in .streamlit/secrets.toml locally).
"""
import streamlit as st
import psycopg2
import psycopg2.extras
from contextlib import contextmanager


@st.cache_resource
def get_connection_pool():
    """A single cached connection is fine for Streamlit's low-concurrency use case."""
    conn = psycopg2.connect(st.secrets["postgres_url"])
    conn.autocommit = True
    return conn


@contextmanager
def get_cursor(dict_cursor=True):
    conn = get_connection_pool()
    cursor_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
    cur = conn.cursor(cursor_factory=cursor_factory)
    try:
        yield cur
    except psycopg2.Error:
        conn.rollback()
        raise
    finally:
        cur.close()


def query(sql, params=None, fetch="all"):
    """Run a SELECT and return rows as list of dicts (or a single dict)."""
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        if fetch == "all":
            return cur.fetchall()
        elif fetch == "one":
            return cur.fetchone()
        return None


def execute(sql, params=None, returning=False):
    """Run an INSERT/UPDATE/DELETE. If returning=True, returns the RETURNING row."""
    with get_cursor() as cur:
        cur.execute(sql, params or ())
        if returning:
            return cur.fetchone()
        return None


def execute_many(sql, param_list):
    """Bulk insert/update helper."""
    with get_cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, param_list)
