from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

"""
env.py — configuración de Alembic para Cash Flow Autos.

Alembic genera este archivo solo, pero lo reemplazamos por esta versión para que:
  1. Lea el DATABASE_URL desde el .env (NO lo escribimos hardcodeado: es secreto).
  2. Conozca nuestros modelos (Base.metadata) y así pueda autogenerar migraciones.

>>> Este archivo va en:  app/database/migraciones/env.py
    (pegá TODO este contenido reemplazando el env.py que generó "alembic init").
"""

import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# --- Hacemos que Python encuentre el paquete "app" ---------------------------
# Este env.py vive en  app/database/migraciones/  , así que subimos 3 niveles
# (migraciones -> database -> app -> raíz del proyecto) y agregamos la raíz al
# path de búsqueda de módulos. Si no, "import app..." fallaría.
RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
sys.path.append(str(RAIZ_PROYECTO))

from app.database.models import Base  # noqa: E402  (va después de tocar sys.path)

# --- Cargamos el .env y armamos la URL de conexión ---------------------------
load_dotenv()

config = context.config
# Inyectamos la URL leída del .env dentro de la config de Alembic.
# Leemos la URL del .env y validamos que exista antes de usarla.
url_bd = os.getenv("DATABASE_URL")
if not url_bd:
    raise RuntimeError(
        "No encontré DATABASE_URL. Revisá que el archivo .env exista y tenga esa variable."
    )

# Inyectamos la URL dentro de la config de Alembic.
config.set_main_option("sqlalchemy.url", url_bd)

# Logging por defecto de Alembic.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Esta es la metadata que Alembic compara contra la base para detectar cambios.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera el SQL sin conectarse (modo 'offline'). Rara vez se usa."""
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
    """Se conecta a la base y aplica las migraciones (el modo habitual)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # también detecta cambios de tipo en columnas
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()