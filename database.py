import json
import sqlite3
from pathlib import Path

from config import DATABASE_PATH, DATABASE_URL

DB_PATH = Path(DATABASE_PATH) if DATABASE_PATH else Path(__file__).parent / "reparaciones.db"
USE_POSTGRES = bool(DATABASE_URL)


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


POSTGRES_URL = _normalize_database_url(DATABASE_URL) if DATABASE_URL else ""


def _placeholder() -> str:
    return "%s" if USE_POSTGRES else "?"


def _repuestos_agg_sql() -> str:
    if USE_POSTGRES:
        return """
            COALESCE(
                json_agg(
                    json_build_object('nombre', p.nombre, 'cantidad', p.cantidad)
                ) FILTER (WHERE p.id IS NOT NULL),
                '[]'::json
            )
        """
    return """
        COALESCE(
            json_group_array(
                json_object('nombre', p.nombre, 'cantidad', p.cantidad)
            ) FILTER (WHERE p.id IS NOT NULL),
            '[]'
        )
    """


def get_connection():
    if USE_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(POSTGRES_URL, row_factory=dict_row)
        return conn

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def parse_repuestos(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return list(value)


def migrate_ubt_to_text(conn):
    columns = conn.execute("PRAGMA table_info(reparaciones)").fetchall()
    ubt_column = next((column for column in columns if column[1] == "ubt"), None)
    if not ubt_column or ubt_column[2].upper() == "TEXT":
        return

    conn.executescript(
        """
        CREATE TABLE reparaciones_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ubt TEXT NOT NULL,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            tecnico TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            tiempo_estimado_minutos INTEGER,
            maquina TEXT
        );

        INSERT INTO reparaciones_new (
            id, ubt, fecha, descripcion, tecnico, created_at, tiempo_estimado_minutos, maquina
        )
        SELECT
            id,
            CAST(ubt AS TEXT),
            fecha,
            descripcion,
            tecnico,
            created_at,
            tiempo_estimado_minutos,
            maquina
        FROM reparaciones;

        DROP TABLE reparaciones;
        ALTER TABLE reparaciones_new RENAME TO reparaciones;
        CREATE INDEX IF NOT EXISTS idx_reparaciones_ubt ON reparaciones (ubt);
        CREATE INDEX IF NOT EXISTS idx_reparaciones_fecha ON reparaciones (fecha);
        """
    )


def _init_sqlite():
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reparaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ubt TEXT NOT NULL,
                fecha TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                tecnico TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS repuestos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reparacion_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1 CHECK (cantidad > 0),
                FOREIGN KEY (reparacion_id) REFERENCES reparaciones (id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_reparaciones_ubt ON reparaciones (ubt);
            CREATE INDEX IF NOT EXISTS idx_reparaciones_fecha ON reparaciones (fecha);
            """
        )
        migrate_ubt_to_text(conn)

        columns = {row[1] for row in conn.execute("PRAGMA table_info(reparaciones)").fetchall()}
        if "tiempo_estimado_minutos" not in columns:
            conn.execute(
                "ALTER TABLE reparaciones ADD COLUMN tiempo_estimado_minutos INTEGER CHECK (tiempo_estimado_minutos > 0)"
            )
        if "maquina" not in columns:
            conn.execute("ALTER TABLE reparaciones ADD COLUMN maquina TEXT")


def _init_postgres():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reparaciones (
                id SERIAL PRIMARY KEY,
                ubt TEXT NOT NULL,
                fecha TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                tecnico TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')),
                tiempo_estimado_minutos INTEGER CHECK (tiempo_estimado_minutos > 0),
                maquina TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS repuestos (
                id SERIAL PRIMARY KEY,
                reparacion_id INTEGER NOT NULL REFERENCES reparaciones (id) ON DELETE CASCADE,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL DEFAULT 1 CHECK (cantidad > 0)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reparaciones_ubt ON reparaciones (ubt)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reparaciones_fecha ON reparaciones (fecha)")


def init_db():
    if USE_POSTGRES:
        _init_postgres()
    else:
        _init_sqlite()


def fetch_reparaciones(ubt=None, fecha=None, tecnico=None, maquina=None):
    ph = _placeholder()
    query = f"""
        SELECT
            r.id,
            r.ubt,
            r.fecha,
            r.descripcion,
            r.tecnico,
            r.maquina,
            r.tiempo_estimado_minutos,
            r.created_at,
            {_repuestos_agg_sql()} AS repuestos
        FROM reparaciones r
        LEFT JOIN repuestos p ON p.reparacion_id = r.id
        WHERE 1 = 1
    """
    params = []
    if ubt is not None:
        query += f" AND r.ubt = {ph}"
        params.append(ubt)
    if fecha:
        query += f" AND r.fecha = {ph}"
        params.append(fecha)
    if tecnico:
        query += f" AND r.tecnico = {ph}"
        params.append(tecnico)
    if maquina:
        query += f" AND r.maquina = {ph}"
        params.append(maquina)
    query += " GROUP BY r.id ORDER BY r.created_at DESC, r.id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows


def fetch_reparacion_by_id(reparacion_id):
    ph = _placeholder()
    query = f"""
        SELECT
            r.id,
            r.ubt,
            r.fecha,
            r.descripcion,
            r.tecnico,
            r.maquina,
            r.tiempo_estimado_minutos,
            r.created_at,
            {_repuestos_agg_sql()} AS repuestos
        FROM reparaciones r
        LEFT JOIN repuestos p ON p.reparacion_id = r.id
        WHERE r.id = {ph}
        GROUP BY r.id
    """
    with get_connection() as conn:
        return conn.execute(query, (reparacion_id,)).fetchone()


def insert_reparacion(
    ubt,
    fecha,
    descripcion,
    tecnico,
    maquina,
    tiempo_estimado_minutos,
    repuestos,
):
    ph = _placeholder()
    with get_connection() as conn:
        if USE_POSTGRES:
            row = conn.execute(
                f"""
                INSERT INTO reparaciones (ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                RETURNING id
                """,
                (ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos),
            ).fetchone()
            reparacion_id = row["id"]
        else:
            cursor = conn.execute(
                f"""
                INSERT INTO reparaciones (ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos)
                VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """,
                (ubt, fecha, descripcion, tecnico, maquina, tiempo_estimado_minutos),
            )
            reparacion_id = cursor.lastrowid

        for repuesto in repuestos:
            conn.execute(
                f"""
                INSERT INTO repuestos (reparacion_id, nombre, cantidad)
                VALUES ({ph}, {ph}, {ph})
                """,
                (reparacion_id, repuesto["nombre"], repuesto["cantidad"]),
            )

    return fetch_reparacion_by_id(reparacion_id)


def fetch_resumen_counts():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT ubt, COUNT(*) AS total
            FROM reparaciones
            GROUP BY ubt
            ORDER BY ubt
            """
        ).fetchall()
    return rows


def fetch_resumen_hoy_counts(fecha, ubt=None):
    ph = _placeholder()
    query = """
        SELECT ubt, COUNT(*) AS total
        FROM reparaciones
        WHERE fecha = """
    query += ph
    params = [fecha]
    if ubt is not None:
        query += f" AND ubt = {ph}"
        params.append(ubt)
    query += " GROUP BY ubt ORDER BY ubt"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows


def fetch_tiempo_total_hoy(fecha, ubt=None):
    ph = _placeholder()
    query = """
        SELECT COALESCE(SUM(tiempo_estimado_minutos), 0) AS tiempo_total
        FROM reparaciones
        WHERE fecha = """
    query += ph
    params = [fecha]
    if ubt is not None:
        query += f" AND ubt = {ph}"
        params.append(ubt)

    with get_connection() as conn:
        return conn.execute(query, params).fetchone()["tiempo_total"]
