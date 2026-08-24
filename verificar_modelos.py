"""
verificar_modelos.py
=====================
Chequeo rápido de que los modelos están bien definidos, SIN tocar la base real.
Sirve para detectar errores de tipeo o de relaciones antes de correr Alembic.

Correr desde la raíz del proyecto:  py verificar_modelos.py
"""

from sqlalchemy.orm import configure_mappers

from app.database.models import Base

# configure_mappers() fuerza a SQLAlchemy a validar TODAS las relaciones entre
# tablas. Si algo está mal enlazado, revienta acá con un error claro.
configure_mappers()

print("✓ Los modelos cargaron correctamente.\n")
print("Tablas detectadas:")
for tabla in Base.metadata.sorted_tables:
    print(f"  - {tabla.name:20} ({len(tabla.columns)} columnas)")
