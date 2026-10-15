"""seed do cardapio inicial

Revision ID: adf71a1b6b9d
Revises: 718ca2554f87
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "adf71a1b6b9d"
down_revision: Union[str, Sequence[str], None] = "718ca2554f87"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CAFES = [
    {"nome": "Bourbon Amarelo", "preco": 12.50},
    {"nome": "Catuaí Vermelho", "preco": 10.00},
    {"nome": "Mundo Novo", "preco": 9.50},
    {"nome": "Geisha", "preco": 24.00},
    {"nome": "Arara", "preco": 14.00},
]


def upgrade() -> None:
    cafes = sa.table(
        "cafes",
        sa.column("nome", sa.String),
        sa.column("preco", sa.Numeric),
    )
    op.bulk_insert(cafes, CAFES)


def downgrade() -> None:
    nomes = ", ".join(f"'{c['nome']}'" for c in CAFES)
    op.execute(f"DELETE FROM cafes WHERE nome IN ({nomes})")
