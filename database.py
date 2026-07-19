import sqlite3
from pathlib import Path

from config import DATABASE_PATH

DB_PATH = Path(DATABASE_PATH) if DATABASE_PATH else Path(__file__).parent / "reparaciones.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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


def init_db():
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
