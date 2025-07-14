from alembic.config import Config
from alembic import command

def run_migrations(apply_only=True):
    # Use existing alembic.ini and .env (env.py handles DB URL)
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("script_location", "alembic")

    if not apply_only:
        command.revision(alembic_cfg, message="Auto migration", autogenerate=True)

    command.upgrade(alembic_cfg, "head")
