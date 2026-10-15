"""adiciona coluna origem

Revision ID: 2db963af808b
Revises: adf71a1b6b9d
Create Date: 2026-10-15 20:34:05.607577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2db963af808b'
down_revision: Union[str, Sequence[str], None] = 'adf71a1b6b9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # EXPANDIR: coluna nova com valor padrão.
    # Linhas existentes recebem o padrão; o código antigo continua funcionando.
    op.add_column(
        "cafes",
        sa.Column(
            "origem",
            sa.String(60),
            nullable=False,
            server_default="Não informada",
        ),
    )
    # MIGRAR: preenche os dados existentes, sem apagar nada.
    op.execute(
        "UPDATE cafes SET origem = 'Cerrado Mineiro' "
        "WHERE nome IN ('Bourbon Amarelo', 'Catuaí Vermelho', 'Arara')"
    )
    op.execute(
        "UPDATE cafes SET origem = 'Chapada Diamantina' "
        "WHERE nome IN ('Mundo Novo', 'Geisha')"
    )


def downgrade() -> None:
    op.drop_column("cafes", "origem")
