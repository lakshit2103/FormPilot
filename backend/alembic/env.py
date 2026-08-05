from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# FormPilot AI – Alembic migration environment
# This file makes Alembic aware of our async SQLAlchemy setup and all ORM models.

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so metadata is populated
from app.core.database import Base  # noqa: F401
import app.models  # noqa: F401 — triggers __init__ imports

target_metadata = Base.metadata


def get_url() -> str:
    from app.core.config import settings
    # Alembic uses the sync driver; swap asyncpg -> psycopg2
    return settings.DATABASE_URL.replace("+asyncpg", "")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
