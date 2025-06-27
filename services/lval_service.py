'''import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.db.oracle import execute_query

logger = logging.getLogger(__name__)

class LvalConfig:
    """
    Permite cargar la tabla ACSELD.LVAL como un diccionario {CODLVAL: descrip_desencriptado},
    para usar de forma similar a una configuración.
    Cachea los resultados en memoria para llamadas subsecuentes.
    """
    _cache: Optional[Dict[str, Any]] = None

    @classmethod
    async def load(cls, tipolval: str) -> Dict[str, Any]:
        """
        Carga una sola vez el mapeo CODLVAL -> DESCRIP (desencriptado) y lo cachea.
        """
        if cls._cache is None:
            sql =
                SELECT CODLVAL, Encrypt_pkg.DECRYPT(DESCRIP) AS DESCRIP_DECRYPTED
                  FROM ACSELD.LVAL
                 WHERE TIPOLVAL = :tipolval
                   AND STSLVAL  = 'ACT'

            params = {'tipolval': tipolval}
            rows = await execute_query(sql, params)

            cls._cache = {r['CODLVAL']: r['DESCRIP_DECRYPTED'] for r in rows}
            logger.debug('Cached LvalConfig: %s', cls._cache)
        return cls._cache

    @classmethod
    async def get(cls, key: str, default: Any = None) -> Any:
        """
        Obtiene la DESCRIP desencriptada asociada al CODLVAL dado, o el valor por defecto si no existe.
        Usa el caché si ya se cargó.
        """
        if cls._cache is None:
            logger.warning(
                "LvalConfig cache not loaded. Please ensure `await LvalConfig.load(your_tipolval)` "
                "is called at application startup or before first use of `get`."
            )
            return default

        # La clave 'key' es el CODLVAL, y el valor recuperado es la DESCRIP desencriptada.
        return cls._cache.get(key, default)'''

import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.db.oracle import execute_query

logger = logging.getLogger(__name__)

class LvalConfig:
    """
    Permite cargar la tabla ACSELD.LVAL como un diccionario {CODLVAL: descrip_desencriptado},
    para usar de forma similar a una configuración.
    Cachea los resultados en memoria para llamadas subsecuentes.
    """
    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    async def load(cls, tipolval: str, db_name: str) -> Dict[str, Any]: # Añade db_name
        """
        Carga una sola vez el mapeo CODLVAL -> DESCRIP (desencriptado) y lo cachea
        para un `tipolval` y `db_name` específicos.
        """
        cache_key = (db_name, tipolval) # Clave de caché compuesta

        if cache_key not in cls._cache: # Comprueba si ya está en caché
            sql = '''
                SELECT CODLVAL, Encrypt_pkg.DECRYPT(DESCRIP) AS DESCRIP_DECRYPTED
                  FROM ACSELD.LVAL
                 WHERE TIPOLVAL = :tipolval
                   AND STSLVAL  = 'ACT'
            '''
            params = {'tipolval': tipolval}
            rows = await execute_query(sql, params, db_name=db_name)

            cls._cache[cache_key] = {r['CODLVAL']: r['DESCRIP_DECRYPTED'] for r in rows}
            logger.debug('Cached LvalConfig for %s: %s', cache_key, cls._cache[cache_key])
        return cls._cache[cache_key]

    @classmethod
    async def get(cls, key: str, tipolval: str, db_name: str, default: Any = None) -> Any: # Añade tipolval y db_name
        """
        Obtiene la DESCRIP desencriptada asociada al CODLVAL dado, o el valor por defecto si no existe.
        Usa el caché si ya se cargó. Requiere tipolval y db_name para la clave de caché.
        """
        cache_key = (db_name, tipolval)

        if cache_key not in cls._cache:
            logger.warning(
                "LvalConfig cache for %s not loaded. Please ensure `await LvalConfig.load(tipolval, db_name)` "
                "is called at application startup or before first use of `get`.", cache_key
            )
            return default

        return cls._cache[cache_key].get(key, default)