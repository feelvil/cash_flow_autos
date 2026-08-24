"""
conexion.py
===========
Punto ÚNICO de conexión a la base de datos PostgreSQL (Neon).

Acá creamos dos cosas que usa toda la app:

  - engine: el "motor" que sabe cómo hablar con Neon. Lee el DATABASE_URL del .env.
  - SessionLocal: una fábrica de sesiones. Una sesión es como una "conversación"
    con la base: la abrís, hacés consultas o cambios, y la cerrás.

El resto de la aplicación NO se conecta por su cuenta: siempre le pide una sesión
a este módulo. Así hay un solo lugar donde se configura la conexión.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Carga las variables del archivo .env (entre ellas, DATABASE_URL).
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Si falta la variable, cortamos con un mensaje claro en vez de un error raro.
    raise RuntimeError(
        "No encontré DATABASE_URL. Revisá que el archivo .env exista y tenga esa variable."
    )

# El engine mantiene un "pool" de conexiones reutilizables.
#   - pool_pre_ping=True: antes de usar una conexión, verifica que siga viva.
#     Es muy útil con bases en la nube como Neon, que cierran conexiones ociosas
#     (si no, a veces la primera consulta del día fallaría).
#   - echo=False: no imprime cada SQL. Ponelo en True si querés ver qué manda.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# Fábrica de sesiones. En la lógica de negocio la usamos así:
#
#     from app.database.conexion import SessionLocal
#     with SessionLocal() as sesion:
#         ...  # consultas y cambios
#         sesion.commit()
#
#   - autoflush=False: no manda cambios a la base hasta que hagamos commit
#     (más predecible mientras aprendemos).
#   - expire_on_commit=False: después del commit, los objetos siguen usables
#     sin volver a consultar la base.
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False
)
