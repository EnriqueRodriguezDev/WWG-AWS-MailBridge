import re


def fix_html_body(html_body: str) -> str:
    """
    Escapa comillas dobles dentro de contenido HTML, preservando las que ya están escapadas.

    Args:
        html_body (str): Cadena HTML con posibles comillas sin escapar

    Returns:
        str: HTML con comillas internas correctamente escapadas
    """
    # Expresión regular para encontrar comillas dobles que NO estén escapadas
    pattern = r'(?<!\\)"'

    # Reemplazar cada comilla no escapada con versión escapada
    return re.sub(pattern, r'\"', html_body)