"""Excepcions de la capa d'aplicació de w2flow."""


class NoActiveFilterConfigError(Exception):
    """Es llança quan no hi ha cap FilterConfig activa a la base de dades.

    El repositori la llança a get_active() quan la consulta no retorna cap registre.
    El exception handler la converteix en una resposta HTTP 404.
    """

    def __init__(self) -> None:
        super().__init__("No hi ha cap configuració de filtre activa a la base de dades.")


class TenderApiError(Exception):
    """Es llança quan la comunicació amb l'API de contractació pública falla.

    El client HTTP la llança capturant errors de xarxa o respostes no 2xx.
    El exception handler la converteix en una resposta HTTP 502.

    Args:
        message: Descripció de l'error tècnic.
    """

    def __init__(self, message: str) -> None:
        super().__init__(f"Error en la comunicació amb l'API externa: {message}")
