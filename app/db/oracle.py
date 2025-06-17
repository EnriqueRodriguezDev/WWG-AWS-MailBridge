import os
import asyncio
import oracledb
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from app.core.config import settings

# Si usas Instant Client, inicialízalo una vez
#CLIENT_LIB_DIR = settings.ORACLE_INSTANT_CLIENT_DIR

CLIENT_LIB_DIR = os.getenv("ORACLE_INSTANT_CLIENT_DIR")
if CLIENT_LIB_DIR and os.path.isdir(CLIENT_LIB_DIR):
    oracledb.init_oracle_client(lib_dir=CLIENT_LIB_DIR)

# Crear pool global de conexiones asíncronas
def _init_pool():
    return oracledb.create_pool(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=f"{settings.DB_HOST}/{settings.DB_SERVICE_NAME}",
        min=2,
        max=10,
        increment=1
    )

_pool: Optional[oracledb.SessionPool] = None

@asynccontextmanager
async def get_connection():
    """
    Context manager asíncrono que obtiene conexiones del pool.
    """
    global _pool
    if _pool is None:
        # Crear el pool en un hilo para no bloquear el loop
        _pool = await asyncio.to_thread(_init_pool)
    # Adquirir conexión
    conn = await asyncio.to_thread(_pool.acquire)
    try:
        yield conn
    finally:
        # Liberar conexión al pool
        await asyncio.to_thread(_pool.release, conn)

'''@asynccontextmanager
async def get_connection():
    """
    Context manager asíncrono para oracledb.Connection.
    Usa asyncio.to_thread para no bloquear el loop.
    """
    conn = oracledb.connect(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        dsn=f"{settings.DB_HOST}/{settings.DB_SERVICE_NAME}",
    )
    try:
        yield conn
    finally:
        await asyncio.to_thread(conn.close)'''

async def execute_query(
    sql: str,
    params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Ejecuta un SELECT y devuelve lista de dicts.
    """
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.cursor)
        await asyncio.to_thread(cursor.execute, sql, params or {})
        cols = [col[0] for col in cursor.description]
        rows = await asyncio.to_thread(cursor.fetchall)
        return [dict(zip(cols, row)) for row in rows]


async def call_proc_update(
        proc_name: str,
        params: List[Any]
) -> int:
    """
    Invoca un PROCEDURE que devuelve un OUT NUMBER al final.
    Retorna el valor de ese OUT NUMBER.
    """
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.cursor)
        out_var = cursor.var(oracledb.DB_TYPE_NUMBER)
        args = params + [out_var]

        # Llamada al SP, ignoramos el 'result' que a veces viene como int
        await asyncio.to_thread(cursor.callproc, proc_name, args)
        await asyncio.to_thread(conn.commit)

        # Aquí sí extraemos el valor directamente del Var
        return int(out_var.getvalue() or 0)

async def call_proc_fetch(
    proc_name: str,
    params: List[Any],
    out_cursor_pos: int
) -> List[Dict[str, Any]]:
    """
    Invoca un PROCEDURE que tiene un REF CURSOR en la posición out_cursor_pos.
    Ej:
      PROCEDURE PR_BUSCA_LVL(p1 IN ..., p2 IN ..., p3 OUT SYS_REFCURSOR);
      --> out_cursor_pos = 2
    Devuelve los registros del cursor como lista de dicts.
    """
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.cursor)
        refcur = cursor.var(oracledb.DB_TYPE_CURSOR)
        # inserta el var en la lista de params
        args = list(params)
        args.insert(out_cursor_pos, refcur)
        await asyncio.to_thread(cursor.callproc, proc_name, args)
        async_cursor = refcur.getvalue()
        cols = [c[0] for c in async_cursor.description]
        rows = await asyncio.to_thread(async_cursor.fetchall)
        return [dict(zip(cols, row)) for row in rows]