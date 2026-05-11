"""create tenders and filter_configs tables

Revision ID: 0001
Revises:
Create Date: 2026-05-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea les taules tenders i filter_configs."""
    op.create_table(
        "tenders",
        sa.Column("expedient_id", sa.String(),
                  primary_key=True, nullable=False),
        sa.Column("publicacio_id", sa.Integer(), nullable=False),
        sa.Column("organ", sa.Text(), nullable=False),
        sa.Column("titol", sa.Text(), nullable=False),
        sa.Column("codi_expedient", sa.String(), nullable=True),
        sa.Column("pressupost", sa.Float(), nullable=True),
        sa.Column("cpv_principal", sa.String(20), nullable=True),
        sa.Column("data_limit", sa.DateTime(timezone=True), nullable=True),
        sa.Column("durada_dies", sa.Integer(), nullable=True),
        sa.Column("tipus_contracte_id", sa.Integer(), nullable=True),
        sa.Column("procediment_id", sa.Integer(), nullable=True),
        sa.Column("nuts_code", sa.String(10), nullable=True),
        sa.Column("classifications", sa.ARRAY(sa.String()), nullable=False),
    )

    op.create_table(
        "filter_configs",
        sa.Column("id", sa.Integer(), primary_key=True,
                  autoincrement=True, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tipus_expedient", sa.Integer(), nullable=False),
        sa.Column("fase_vigent", sa.Integer(), nullable=False),
        sa.Column("ambit", sa.Integer(), nullable=True),
        sa.Column("tipus_contracte", sa.Integer(), nullable=True),
        sa.Column("procediment_adjudicacio", sa.Integer(), nullable=True),
        sa.Column("cpv_codes", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("pressupost_maxim", sa.Float(), nullable=False),
        sa.Column("nuts_codes", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("classifications", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("durada_minima_dies", sa.Integer(), nullable=False),
        sa.Column("durada_maxima_dies", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Elimina les taules filter_configs i tenders."""
    op.drop_table("filter_configs")
    op.drop_table("tenders")
