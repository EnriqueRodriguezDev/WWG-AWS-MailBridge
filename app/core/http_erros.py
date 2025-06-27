from fastapi import HTTPException, status

class HttpErrors:
    """
    Clase de utilidad para generar excepciones HTTP de forma reutilizable y consistente.
    Cada método crea una HTTPException con el código de estado HTTP apropiado
    y un mensaje de detalle predeterminado, que puede ser sobrescrito.
    """

    @staticmethod
    def bad_request(detail: str = "Solicitud inválida. Verifique los datos enviados.") -> HTTPException:
        """
        Genera una excepción 400 Bad Request.
        Indica que el servidor no pudo entender la solicitud debido a una sintaxis inválida.
        """
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    @staticmethod
    def unauthorized(detail: str = "Credenciales de autenticación inválidas o faltantes.") -> HTTPException:
        """
        Genera una excepción 401 Unauthorized.
        Indica que la autenticación es requerida y ha fallado o no ha sido proporcionada.
        """
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}, # Común para errores de autenticación JWT
        )

    @staticmethod
    def forbidden(detail: str = "No tienes permiso para acceder a este recurso o realizar esta acción.") -> HTTPException:
        """
        Genera una excepción 403 Forbidden.
        Indica que el servidor entiende la solicitud pero se niega a autorizarla.
        """
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

    @staticmethod
    def not_found(detail: str = "El recurso solicitado no fue encontrado.") -> HTTPException:
        """
        Genera una excepción 404 Not Found.
        Indica que el servidor no pudo encontrar el recurso solicitado.
        """
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

    @staticmethod
    def method_not_allowed(detail: str = "Método HTTP no permitido para este recurso.") -> HTTPException:
        """
        Genera una excepción 405 Method Not Allowed.
        Indica que el método HTTP utilizado no es soportado por el recurso.
        """
        return HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=detail
        )

    @staticmethod
    def conflict(detail: str = "El recurso ya existe o hay un conflicto en el estado actual del recurso.") -> HTTPException:
        """
        Genera una excepción 409 Conflict.
        Indica un conflicto con el estado actual del recurso, por ejemplo, un intento de crear un recurso duplicado.
        """
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )

    @staticmethod
    def unprocessable_entity(detail: str = "La entidad no pudo ser procesada debido a errores de validación semántica.") -> HTTPException:
        """
        Genera una excepción 422 Unprocessable Entity.
        Común para errores de validación de datos donde la sintaxis es correcta, pero la semántica es incorrecta.
        """
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

    @staticmethod
    def internal_server_error(detail: str = "Un error inesperado ha ocurrido en el servidor. Por favor, inténtelo de nuevo más tarde.") -> HTTPException:
        """
        Genera una excepción 500 Internal Server Error.
        Indica una condición de error genérica en el servidor.
        """
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

    @staticmethod
    def service_unavailable(detail: str = "El servicio no está disponible temporalmente. Por favor, inténtelo de nuevo más tarde.") -> HTTPException:
        """
        Genera una excepción 503 Service Unavailable.
        Indica que el servidor no puede manejar la solicitud temporalmente, quizás debido a una sobrecarga o mantenimiento.
        """
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

    @staticmethod
    def gateway_timeout(detail: str = "El servidor no recibió una respuesta a tiempo de un servidor ascendente.") -> HTTPException:
        """
        Genera una excepción 504 Gateway Timeout.
        Indica que un servidor actuando como gateway o proxy no recibió una respuesta a tiempo.
        """
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=detail
        )