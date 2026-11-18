from alembic import context
from sqlalchemy import engine_from_config, pool
from sipan import config
from sipan.persistence.database import Base
from sipan.persistence import models  # noqa: F401

target_metadata = Base.metadata
configuration = context.config
configuration.set_main_option("sqlalchemy.url", config.DATABASE_MIGRATION_URL or "")

def run_migrations_offline():
    context.configure(url=configuration.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(configuration.get_section(configuration.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction(): context.run_migrations()

if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
