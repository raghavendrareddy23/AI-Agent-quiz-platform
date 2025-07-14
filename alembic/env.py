from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

import os
import sys
from dotenv import load_dotenv

# Load .env and your app modules
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from app.models.database import Base
from app.models import user, quiz  # All models must be imported

# ✅ This provides metadata for autogenerate support
target_metadata = Base.metadata

# ✅ DO NOT DO THIS: config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
# It causes interpolation error due to `%` in ODBC string

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline():
    url = settings.DATABASE_URL  # ✅ use directly
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
