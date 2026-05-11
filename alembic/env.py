"""Configuració d'Alembic per a les migracions de w2flow.

Importa Base i tots els models per garantir que autogenerate els detecta.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import Settings
from app.infrastructure.database import Base

# Importem els models perquè SQLAlchemy registri les taules al metadata
import app.infrastructure.models.tender_model  # noqa: F401
import app.infrastructure.models.filter_config_model  # noqa: F401

# Objecte de configuració d'Alembic
config = context.config

# Injectem la URL de BD des de Settings (sobreposa la del .ini)
_settings = Settings()
config.set_main_option("sqlalchemy.url", _settings.database_url)

# Configuració de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata que Alembic compararà per generar les migracions
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa les migracions en mode offline (sense connexió real).

    Útil per generar SQL pur sense necessitat d'una BD accessible.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa les migracions en mode online (amb connexió real a PostgreSQL)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
