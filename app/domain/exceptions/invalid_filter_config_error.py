"""Excepcions de configuració de filtres del domini de w2flow."""


class InvalidFilterConfigError(ValueError):
    """Es llança quan un camp de FilterConfig té un valor fora del rang vàlid.

    Args:
        field:     Nom del camp amb el valor invàlid.
        value:     Valor rebut.
        min_value: Valor mínim permès per al camp.
        max_value: Valor màxim permès per al camp.
    """

    def __init__(self, field: str, value: int, min_value: int, max_value: int) -> None:
        super().__init__(
            f"Camp '{field}' amb valor {value} fora del rang vàlid [{min_value}, {max_value}]."
        )
