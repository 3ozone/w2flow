"""Excepcions del domini de w2flow."""


class InvalidScoreError(ValueError):
    """Es llança quan un criteri de puntuació NLP està fora del rang vàlid (RN-12).

    Args:
        field:  Nom del camp amb el valor invàlid.
        value:  Valor rebut.
        max_value: Valor màxim permès per al camp.
    """

    def __init__(self, field: str, value: int, max_value: int) -> None:
        super().__init__(
            f"Camp '{field}' amb valor {value} fora del rang vàlid [0, {max_value}]."
        )
