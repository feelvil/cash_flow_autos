"""
Módulo de conexión: configurar SQLAlchemy y crear sesiones a la BD.

Usa:
- DATABASE_URL desde .env
- psycopg2-binary para PostgreSQL
- SessionLocal() para crear sesiones
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ============================================================================
# CONFIGURACIÓN DE CONEXIÓN
# ============================================================================

# Obtener URL de conexión desde .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL no está configurada en .env. "
        "Debe contener algo como: postgresql://usuario:pass@host/db"
    )

# Crear engine de SQLAlchemy
# echo=True para ver las queries en consola (comentar en producción)
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Cambiar a True para ver SQL statements
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    pool_recycle=3600,   # Reciclar conexiones cada hora
)

# Crear SessionLocal para crear sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================================================
# FUNCIONES ÚTILES
# ============================================================================

def get_db() -> Session:
    """
    Obtener una sesión de BD.
    
    Útil para FastAPI o scripts que necesitan una sesión.
    
    Uso:
        db = get_db()
        try:
            # ... usar db
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def probar_conexion() -> bool:
    """
    Probar que la conexión a la BD funciona.
    
    Retorna:
        bool: True si la conexión es OK
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            return result.fetchone() is not None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False


# ============================================================================
# CREAR TABLAS (si no existen)
# ============================================================================

def crear_tablas():
    """
    Crear todas las tablas en la BD (idempotente).
    
    Si las tablas ya existen, no hace nada.
    
    Uso:
        python -c "from app.database.conexion import crear_tablas; crear_tablas()"
    """
    from app.database.models import Base
    
    print("Creando tablas (si no existen)...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas/verificadas")


# ============================================================================
# DEBUG / TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Testing: verificar conexión a BD.
    
    Uso: python -m app.database.conexion
    """
    print("Probando conexión a la BD...")
    print(f"DATABASE_URL: {DATABASE_URL[:50]}..." if DATABASE_URL else "No configurada")
    
    if probar_conexion():
        print("✓ Conexión OK")
    else:
        print("✗ Conexión fallida")
    
    print("\nIntentando crear tablas...")
    try:
        crear_tablas()
        print("✓ Tablas creadas/verificadas")
    except Exception as e:
        print(f"✗ Error: {e}")
