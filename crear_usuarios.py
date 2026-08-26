"""
crear_usuarios.py
=================
Script de UNA sola vez para cargar los usuarios iniciales en la base.

Los crea SIN contraseña (password_hash = NULL) a propósito: cada persona define
su propia clave la primera vez que entra a la app (el login detecta el "primer
ingreso" y le pide crearla). Así no tenés que inventar ni conocer las claves
ajenas.

Cómo correrlo (desde la raíz del proyecto, con el entorno virtual activado):

    py crear_usuarios.py

Es seguro correrlo más de una vez: si un usuario con ese nombre ya existe, lo
saltea (no lo duplica).

IMPORTANTE: antes de correr esto tiene que estar hecha la migración que agrega
la columna password_hash (ver LOGIN_migracion.md).
"""

import sys
from pathlib import Path

# Permite importar app.* desde la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select

from app.database.conexion import SessionLocal
from app.database.models import Usuario


# ═══════════════════════════════════════════════════════════════════════════
# EDITÁ ESTA LISTA con los nombres reales de las personas que van a usar la app.
# ═══════════════════════════════════════════════════════════════════════════
NOMBRES = [
    "Federico Villanueva",
    
    # agregá o sacá los que necesites...
]


def crear_usuarios():
    """Crea los usuarios de NOMBRES que todavía no existan."""
    with SessionLocal() as sesion:
        creados = 0
        existentes = 0

        for nombre in NOMBRES:
            # ¿Ya existe un usuario con ese nombre?
            ya_esta = sesion.scalar(
                select(Usuario).where(Usuario.nombre == nombre)
            )
            if ya_esta:
                print(f"  = Ya existe: {nombre} (id={ya_esta.id})")
                existentes += 1
                continue

            # Crear el usuario (activo, sin contraseña -> primer ingreso la define).
            usuario = Usuario(nombre=nombre, activo=True)
            sesion.add(usuario)
            sesion.flush()  # para obtener el id asignado
            print(f"  + Creado:   {nombre} (id={usuario.id})")
            creados += 1

        sesion.commit()

        print()
        print(f"Listo: {creados} creado(s), {existentes} ya existía(n).")
        print()
        print("Ahora abrí la app, elegí tu nombre en el login y definí tu")
        print("contraseña (es tu primer ingreso).")


if __name__ == "__main__":
    print("Creando usuarios iniciales...")
    print()
    crear_usuarios()
