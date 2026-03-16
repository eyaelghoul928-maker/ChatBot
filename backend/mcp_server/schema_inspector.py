"""
mcp_server/schema_inspector.py
Découvre automatiquement le schéma de N'IMPORTE QUELLE base MariaDB.
Lit les tables, colonnes, types, clés étrangères et valeurs d'enum.
"""
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config import settings
from loguru import logger

_engine = create_async_engine(
    settings.database_url,
    pool_size=3,
    max_overflow=2,
    pool_pre_ping=True,
)


async def get_full_schema() -> dict:
    """
    Retourne le schéma complet de la base sous forme de texte
    lisible par GPT-4o, et sous forme de dict structuré.
    """
    db_name = settings.db_name
    schema_lines = []
    tables_info = {}

    async with _engine.connect() as conn:

        # ── 1. Lister toutes les tables ───────────────────────────────
        result = await conn.execute(text(
            "SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT "
            "FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = :db AND TABLE_TYPE = 'BASE TABLE' "
            "ORDER BY TABLE_NAME",
        ), {"db": db_name})
        tables = result.fetchall()

        if not tables:
            return {"schema": f"Base '{db_name}' vide ou inaccessible.", "nb_tables": 0}

        # ── 2. Pour chaque table, récupérer les colonnes ──────────────
        for (table_name, table_rows, table_comment) in tables:
            col_result = await conn.execute(text(
                "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, "
                "COLUMN_KEY, COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :tbl "
                "ORDER BY ORDINAL_POSITION"
            ), {"db": db_name, "tbl": table_name})
            columns = col_result.fetchall()

            # ── 3. Clés étrangères ────────────────────────────────────
            fk_result = await conn.execute(text(
                "SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                "FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = :tbl "
                "AND REFERENCED_TABLE_NAME IS NOT NULL"
            ), {"db": db_name, "tbl": table_name})
            foreign_keys = {row[0]: (row[1], row[2]) for row in fk_result.fetchall()}

            # ── 4. Construire la description textuelle ────────────────
            col_descriptions = []
            tables_info[table_name] = {"columns": [], "foreign_keys": foreign_keys}

            for col in columns:
                col_name, col_type, nullable, key, default, extra, comment = col
                tags = []
                if key == "PRI":
                    tags.append("PK")
                if key == "UNI":
                    tags.append("UNIQUE")
                if col_name in foreign_keys:
                    ref_table, ref_col = foreign_keys[col_name]
                    tags.append(f"FK→{ref_table}.{ref_col}")
                if extra == "auto_increment":
                    tags.append("AUTO")
                if nullable == "NO" and key != "PRI":
                    tags.append("NOT NULL")

                tag_str = f" [{', '.join(tags)}]" if tags else ""
                comment_str = f" -- {comment}" if comment else ""
                col_descriptions.append(f"  {col_name} {col_type}{tag_str}{comment_str}")

                tables_info[table_name]["columns"].append({
                    "name": col_name,
                    "type": col_type,
                    "key": key,
                    "nullable": nullable == "YES"
                })

            # ── 5. Ligne de table ─────────────────────────────────────
            header = f"TABLE {table_name}"
            if table_comment:
                header += f"  -- {table_comment}"
            if table_rows:
                header += f"  (~{table_rows:,} lignes)"

            schema_lines.append(header)
            schema_lines.extend(col_descriptions)

            # ── 6. Relations (FK) ─────────────────────────────────────
            if foreign_keys:
                for col_name, (ref_table, ref_col) in foreign_keys.items():
                    schema_lines.append(
                        f"  -- RELATION: {table_name}.{col_name} → {ref_table}.{ref_col}"
                    )
            schema_lines.append("")

        # ── 7. Récapitulatif des relations ────────────────────────────
        schema_lines.append("-- RELATIONS ENTRE TABLES:")
        for table_name, info in tables_info.items():
            for col, (ref_table, ref_col) in info.get("foreign_keys", {}).items():
                schema_lines.append(f"-- {table_name}.{col} → {ref_table}.{ref_col}")

    schema_text = "\n".join(schema_lines)
    nb_tables = len(tables)

    logger.info(f"[SCHEMA INSPECTOR] {nb_tables} tables découvertes dans '{db_name}'")

    return {
        "schema": schema_text,
        "nb_tables": nb_tables,
        "tables": list(tables_info.keys()),
        "db_name": db_name,
    }