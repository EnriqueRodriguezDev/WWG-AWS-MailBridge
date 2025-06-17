import logging
import os # Importar os para obtener el nombre del archivo

def setup_logger(name: str | None = None) -> logging.Logger:
    """
    Configura y devuelve un objeto logger.

    Args:
        name (str, optional): El nombre del logger. Si es None, se usará el
                              nombre del archivo que llama a la función.
                              Por ejemplo, __name__ en el archivo principal.

    Returns:
        logging.Logger: Un objeto logger configurado.
    """
    # Si no se proporciona un nombre, intenta inferir el nombre del archivo
    if name is None:
        # Obtiene el nombre del archivo del módulo que llama a esta función
        # Esto es un truco para hacer que el logger.name sea el del módulo real
        import inspect
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_globals['__name__']
        name = caller_name

    logger = logging.getLogger(name)

    # Evita que se añadan múltiples manejadores si la función se llama varias veces
    # para el mismo logger, lo que podría duplicar los mensajes de log.
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(name)-20s %(message)s",
            # Añadir un StreamHandler si no se está usando basicConfig por defecto
            # Esto asegura que los logs vayan a la consola si no hay otra configuración
            handlers=[logging.StreamHandler()]
        )
        # Asegurarse de que el nivel del logger sea el deseado,
        # ya que basicConfig solo afecta al logger root por defecto.
        logger.setLevel(logging.INFO)

    return logger