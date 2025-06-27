import os
import asyncio
import oracledb
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from app.core.config import settings, DatabaseConfig

CLIENT_LIB_DIR = settings.ORACLE_INSTANT_CLIENT_DIR
if CLIENT_LIB_DIR and os.path.isdir(CLIENT_LIB_DIR):
    oracledb.init_oracle_client(lib_dir=CLIENT_LIB_DIR)

_pools: Dict[str, oracledb.SessionPool] = {}
_pools_lock = asyncio.Lock()

async def _init_pool(db_config: DatabaseConfig, db_name: str) -> oracledb.SessionPool:
    """
    Inicializa un pool de conexiones para una configuración de base de datos específica.
    """
    print(f"Inicializando pool para {db_name} con host: {db_config.DB_HOST}, service_name: {db_config.DB_SERVICE_NAME}")

    return oracledb.create_pool(
        user=db_config.DB_USER,
        password=db_config.DB_PASSWORD,
        dsn=f"{db_config.DB_HOST}:{settings.DB_PORT}/{db_config.DB_SERVICE_NAME}",
        min=2,
        max=10,
        increment=1,
        timeout=10,
    )

@asynccontextmanager
async def get_connection(db_name: str):
    """
    Context manager asíncrono que obtiene conexiones del pool para la base de datos especificada.
    """
    global _pools

    if db_name not in settings.AVAILABLE_DATABASES:
        raise ValueError(f"Base de datos '{db_name}' no es una opción válida.")

    db_config = settings.DATABASE_CONNECTIONS.get(db_name)
    if not db_config:
        raise ValueError(f"Configuración no encontrada para la base de datos: {db_name}")

    async with _pools_lock:
        if db_name not in _pools or _pools[db_name] is None:
            _pools[db_name] = await _init_pool(db_config, db_name)

    conn = await asyncio.to_thread(_pools[db_name].acquire)
    try:
        yield conn
    finally:
        await asyncio.to_thread(_pools[db_name].release, conn)


async def execute_query(
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    db_name: str = "SEGQA"
) -> List[Dict[str, Any]]:
    """
    Ejecuta un SELECT y devuelve lista de dicts.
    Requiere el nombre de la base de datos a la que conectarse.
    """
    async with get_connection(db_name=db_name) as conn:
        cursor = await asyncio.to_thread(conn.cursor)
        await asyncio.to_thread(cursor.execute, sql, params or {})
        cols = [col[0] for col in cursor.description]
        rows = await asyncio.to_thread(cursor.fetchall)
        return [dict(zip(cols, row)) for row in rows]


async def call_proc_update(
        proc_name: str,
        params: List[Any],
        db_name: str = "SEGQA"
) -> int:
    """
    Invoca un PROCEDURE que devuelve un OUT NUMBER al final.
    Retorna el valor de ese OUT NUMBER.
    Requiere el nombre de la base de datos a la que conectarse.
    """
    async with get_connection(db_name=db_name) as conn:
        cursor = await asyncio.to_thread(conn.cursor)
        out_var = cursor.var(oracledb.DB_TYPE_NUMBER)
        args = params + [out_var]

        await asyncio.to_thread(cursor.callproc, proc_name, args)
        await asyncio.to_thread(conn.commit)

        return int(out_var.getvalue() or 0)

async def call_proc_fetch(
    proc_name: str,
    params: List[Any],
    out_cursor_pos: int,
    db_name: str = "SEGQA" # Valor predeterminado
) -> List[Dict[str, Any]]:
    """
    Invoca un PROCEDURE que tiene un REF CURSOR en la posición out_cursor_pos.
    Devuelve los registros del cursor como lista de dicts.
    Requiere el nombre de la base de datos a la que conectarse.
    """
    async with get_connection(db_name=db_name) as conn:
        cursor = await asyncio.to_thread(conn.cursor)
        refcur = cursor.var(oracledb.DB_TYPE_CURSOR)
        args = list(params)
        args.insert(out_cursor_pos, refcur)
        await asyncio.to_thread(cursor.callproc, proc_name, args)
        async_cursor = refcur.getvalue()
        cols = [c[0] for c in async_cursor.description]
        rows = await asyncio.to_thread(async_cursor.fetchall)
        return [dict(zip(cols, row)) for row in rows]