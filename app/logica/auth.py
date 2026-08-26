"""
auth.py
=======
Autenticación de usuarios: verificar login, setear y cambiar contraseñas.

Reglas de seguridad que respeta este módulo:
  - La contraseña NUNCA se guarda en texto plano. Se guarda un "hash" con
    bcrypt, que es de una sola vía (no se puede volver atrás) e incluye un
    "salt" aleatorio distinto por usuario (dos usuarios con la misma clave
    tienen hashes diferentes).
  - bcrypt es lento a propósito: eso hace inviable probar millones de claves
    por fuerza bruta.

Casos que maneja:
  - Usuario con contraseña ya seteada -> se valida contra el hash.
  - Usuario sin contraseña (password_hash = NULL) -> "primer ingreso": la app
    puede pedirle que defina una contraseña. verificar_login lo señala aparte.
  - Usuario inactivo -> no puede entrar.
"""

from dataclasses import dataclass

import bcrypt
from sqlalchemy import select

from app.database.conexion import SessionLocal
from app.database.models import Usuario


# ---------------------------------------------------------------------------
# Resultado de un intento de login. Es más claro que devolver True/False/None
# suelto: la UI sabe exactamente qué pasó y actúa en consecuencia.
# ---------------------------------------------------------------------------
@dataclass
class ResultadoLogin:
    ok: bool                    # True si el login fue exitoso
    usuario_id: int | None      # id del usuario si ok, None si no
    nombre: str | None          # nombre del usuario si ok
    necesita_password: bool     # True si el usuario aún no tiene contraseña
    mensaje: str                # texto para mostrar al usuario


# ---------------------------------------------------------------------------
# Helpers de hashing (bcrypt trabaja con bytes; encapsulamos la conversión).
# ---------------------------------------------------------------------------
def hashear_password(password: str) -> str:
    """
    Devuelve el hash bcrypt de una contraseña, listo para guardar en la BD.
    El salt se genera solo y queda incluido dentro del hash.
    """
    password_bytes = password.encode("utf-8")
    hash_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verificar_password(password: str, hash_guardado: str) -> bool:
    """
    Compara una contraseña tipeada contra el hash guardado.
    Devuelve True si coinciden. Nunca lanza si el hash es inválido: devuelve False.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except (ValueError, TypeError):
        # Hash corrupto o formato inesperado -> tratamos como no coincide.
        return False


# ---------------------------------------------------------------------------
# API pública que usa la UI.
# ---------------------------------------------------------------------------
def listar_usuarios_activos() -> list[dict]:
    """
    Devuelve los usuarios activos (para poblar el combo de la pantalla de login).
    Cada uno: {id, nombre, tiene_password}.
    """
    with SessionLocal() as sesion:
        usuarios = sesion.execute(
            select(Usuario).where(Usuario.activo == True).order_by(Usuario.nombre)  # noqa: E712
        ).scalars().all()
        return [
            {
                "id": u.id,
                "nombre": u.nombre,
                "tiene_password": bool(u.password_hash),
            }
            for u in usuarios
        ]


def verificar_login(usuario_id: int, password: str) -> ResultadoLogin:
    """
    Valida el login de un usuario.
    
    Args:
        usuario_id: el usuario que intenta entrar.
        password: la contraseña tipeada.
    
    Retorna un ResultadoLogin con el detalle de qué pasó.
    """
    with SessionLocal() as sesion:
        usuario = sesion.get(Usuario, usuario_id)
        
        # Usuario inexistente o inactivo.
        if usuario is None:
            return ResultadoLogin(False, None, None, False, "El usuario no existe.")
        if not usuario.activo:
            return ResultadoLogin(False, None, None, False, "El usuario está inactivo.")
        
        # Usuario sin contraseña configurada -> primer ingreso.
        if not usuario.password_hash:
            return ResultadoLogin(
                False, usuario.id, usuario.nombre, True,
                "Este usuario todavía no tiene contraseña. Definí una para continuar."
            )
        
        # Verificar la contraseña.
        if verificar_password(password, usuario.password_hash):
            return ResultadoLogin(
                True, usuario.id, usuario.nombre, False,
                f"Bienvenido, {usuario.nombre}."
            )
        else:
            return ResultadoLogin(
                False, usuario.id, usuario.nombre, False,
                "Contraseña incorrecta."
            )


def establecer_password(usuario_id: int, password_nueva: str) -> bool:
    """
    Setea (o cambia) la contraseña de un usuario. Sirve tanto para el "primer
    ingreso" (definir por primera vez) como para un cambio posterior.
    
    Devuelve True si se guardó bien.
    """
    if not password_nueva or len(password_nueva) < 4:
        raise ValueError("La contraseña debe tener al menos 4 caracteres.")
    
    with SessionLocal() as sesion:
        usuario = sesion.get(Usuario, usuario_id)
        if usuario is None:
            raise ValueError("El usuario no existe.")
        
        usuario.password_hash = hashear_password(password_nueva)
        sesion.commit()
        return True


def cambiar_password(usuario_id: int, password_actual: str, password_nueva: str) -> bool:
    """
    Cambia la contraseña validando primero la actual (para un usuario ya logueado
    que quiere cambiarla desde opciones). Lanza ValueError si la actual no coincide.
    """
    with SessionLocal() as sesion:
        usuario = sesion.get(Usuario, usuario_id)
        if usuario is None:
            raise ValueError("El usuario no existe.")
        if not usuario.password_hash or not verificar_password(password_actual, usuario.password_hash):
            raise ValueError("La contraseña actual es incorrecta.")
    
    # Si la actual es correcta, delega en establecer_password (valida la nueva).
    return establecer_password(usuario_id, password_nueva)


# ---------------------------------------------------------------------------
# Prueba rápida:  py -m app.logica.auth
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Usuarios activos:")
    for u in listar_usuarios_activos():
        estado = "con contraseña" if u["tiene_password"] else "SIN contraseña"
        print(f"  [{u['id']}] {u['nombre']} ({estado})")
