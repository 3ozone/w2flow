"""update filter_configs default values for fase_vigent, ambit, tipus_contracte, procediment_adjudicacio (RN-14)

Revision ID: 2b4f9c1e3d7a
Revises: 1830436449a2
Create Date: 2026-05-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2b4f9c1e3d7a"
down_revision: Union[str, None] = "1830436449a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Actualitza els server_default de filter_configs per als valors correctes de l'API (RN-14).

    - fase_vigent:             0 → 30 (Anunci de licitació en termini)
    - ambit:                   NULL → 1500001 (Generalitat de Catalunya)
    - tipus_contracte:         NULL → 395 (Obres)
    - procediment_adjudicacio: NULL → 401 (Obert)

    Nota: el valor 1000040 del catàleg de Dades Mestres NO funciona al paràmetre
    faseVigent de /cerca-avancada. El portal usa valors propis en múltiples de 10.
    """
    op.alter_column(
        "filter_configs",
        "fase_vigent",
        existing_type=sa.Integer(),
        server_default="30",
        existing_nullable=False,
    )
    op.alter_column(
        "filter_configs",
        "ambit",
        existing_type=sa.Integer(),
        server_default="1500001",
        existing_nullable=True,
    )
    op.alter_column(
        "filter_configs",
        "tipus_contracte",
        existing_type=sa.Integer(),
        server_default="395",
        existing_nullable=True,
    )
    op.alter_column(
        "filter_configs",
        "procediment_adjudicacio",
        existing_type=sa.Integer(),
        server_default="401",
        existing_nullable=True,
    )


def downgrade() -> None:
    """Reverteix els server_default als valors anteriors (sense default)."""
    op.alter_column(
        "filter_configs",
        "fase_vigent",
        existing_type=sa.Integer(),
        server_default=None,
        existing_nullable=False,
    )
    op.alter_column(
        "filter_configs",
        "ambit",
        existing_type=sa.Integer(),
        server_default=None,
        existing_nullable=True,
    )
    op.alter_column(
        "filter_configs",
        "tipus_contracte",
        existing_type=sa.Integer(),
        server_default=None,
        existing_nullable=True,
    )
    op.alter_column(
        "filter_configs",
        "procediment_adjudicacio",
        existing_type=sa.Integer(),
        server_default=None,
        existing_nullable=True,
    )
