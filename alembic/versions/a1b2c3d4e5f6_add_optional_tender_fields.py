"""add_optional_tender_fields

Revision ID: a1b2c3d4e5f6
Revises: 014817d507cb
Create Date: 2026-05-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5c9b9792acb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional fields to tenders table."""
    op.add_column('tenders', sa.Column('codi_cpv', sa.String(), nullable=True))
    op.add_column('tenders', sa.Column(
        'termini_execucio', sa.String(), nullable=True))
    op.add_column('tenders', sa.Column(
        'data_limit_presentacio', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove optional fields from tenders table."""
    op.drop_column('tenders', 'data_limit_presentacio')
    op.drop_column('tenders', 'termini_execucio')
    op.drop_column('tenders', 'codi_cpv')
