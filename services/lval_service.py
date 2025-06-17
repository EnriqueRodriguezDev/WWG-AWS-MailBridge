# src/services/lval_service.py
import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.db.oracle import execute_query

logger = logging.getLogger(__name__)

class LvalService:
    """
    Servicio para acceder a la tabla WWS.LVAL:
      - Obtener CODLVAL por DESCRIP
      - Obtener DESCLONG por CODLVAL
      - Cargar todo como diccionario opcional
    Filtra siempre por TIPOLVAL = settings.DB_AWS_TIPOLVAL y STSLVAL = 'ACT'.
    """

    @staticmethod
    async def get_codlval(descrip: str) -> Optional[str]:
        """
        Retorna un único CODLVAL para una descripción corta dada.
        """
        sql = '''
            SELECT CODLVAL
              FROM ACSELD.LVAL
             WHERE TIPOLVAL = :tipolval
               AND DESCRIP  = :descrip
               AND STSLVAL  = 'ACT'
        '''
        params = {'tipolval': settings.DB_AWS_TIPOLVAL, 'descrip': descrip}
        rows = await execute_query(sql, params)
        if not rows:
            logger.debug('No CODLVAL para descrip=%s', descrip)
            return None
        codlval = rows[0]['CODLVAL']
        logger.debug('Found CODLVAL=%s for DESCRIP=%s', codlval, descrip)
        return codlval

    @staticmethod
    async def get_desclong(codlval: str) -> Optional[str]:
        """
        Retorna la descripción larga (DESCLONG) para un CODLVAL dado.
        """
        sql = '''
            SELECT DESCLONG
              FROM ACSELD.LVAL
             WHERE TIPOLVAL = :tipolval
               AND CODLVAL  = :codlval
               AND STSLVAL  = 'ACT'
        '''
        params = {'tipolval': settings.DB_AWS_TIPOLVAL, 'codlval': codlval}
        rows = await execute_query(sql, params)
        if not rows:
            logger.debug('No DESCLONG para codlval=%s', codlval)
            return None
        desclong = rows[0]['DESCLONG']
        logger.debug('Found DESCLONG for CODLVAL=%s: %s', codlval, desclong)
        return desclong

    @staticmethod
    async def load_all(tipolval: str) -> Dict[str, Any]:
        """
        Carga .
        """
        sql = '''
            SELECT CODLVAL, DESCLONG
              FROM ACSELD.LVAL
             WHERE TIPOLVAL = :tipolval
               AND STSLVAL  = 'ACT'
        '''
        params = {'tipolval': tipolval}
        rows = await execute_query(sql, params)
        codlvals = [r['CODLVAL'] for r in rows]
        logger.debug('Loaded %d CODLVALs', len(codlvals))
        return codlvals

class LvalConfig:
    """
    Permite cargar la tabla WWS.LVAL como un diccionario {descrip: codlval},
    para usar igual que StrategyConfig: cfg = await LvalConfig.load(), cfg.get(descrip).
    Cachea los resultados en memoria para llamadas subsecuentes.
    """
    _cache: Optional[Dict[str, Any]] = None

    @classmethod
    async def load(cls, tipolval: str) -> Dict[str, Any]:
        """
        Carga una sola vez el mapeo DESCRIP -> CODLVAL y lo cachea.
        """
        if cls._cache is None:
            sql = '''
                SELECT DESCRIP, CODLVAL
                  FROM ACSELD.LVAL
                 WHERE TIPOLVAL = :tipolval
                   AND STSLVAL  = 'ACT'
            '''
            params = {'tipolval': tipolval}
            rows = await execute_query(sql, params)
            cls._cache = {r['DESCRIP']: r['CODLVAL'] for r in rows}
            logger.debug('Cached LvalConfig: %s', cls._cache)
        return cls._cache

    @classmethod
    async def get(cls, key: str, default: Any = None) -> Any:
        """
        Obtiene el CODLVAL asociado a la DESCRIP dada, o default si no existe.
        Usa cache si ya se cargó.
        """
        cfg = await cls.load()
        return cfg.get(key, default)