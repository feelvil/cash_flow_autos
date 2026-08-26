"""
Módulo de autenticación: login, hashing de contraseñas con bcrypt, cambio de contraseña.

Funciones principales:
- listar_usuarios_activos(): para poblar combos en login
- verificar_login(usuario_id, password): validar entrada en login
- establecer_password(usuario_id, password): para primer ingreso (admin)
- cambiar_password(usuario_id, password_actual, password_nueva): usuario autoservicio

Las contraseñas NUNCA se guardan en texto plano.
Se usa bcrypt: hashing con salt único por usuario, lento a propósito.
"""

import bcrypt
from sqlalchemy.orm import Session

from app.database.conexion import SessionLocal
from app.database.models import Usuario


# ============================================================================
# EXCEPCIONES PERSONALIZADAS
# ============================================================================

class ErrorDeNegocio(Exception):
    """Excepción para errores esperados de negocio (contraseña incorrecta, etc.)."""
    pass


# ============================================================================
# FUNCIONES DE UTILIDAD: HASHING
# ============================================================================

def _hash_password(password: str) -> str:
    """
    Hashear una contraseña usando bcrypt.
    
    Args:
        password (str): Contraseña en texto plano
    
    Retorna:
        str: Hash seguro de la contraseña (bytes codificados como string UTF-8)
    
    Nota:
        bcrypt es lento a propósito (~0.3s) para dificultar ataques de fuerza bruta.
    """
    # Generar salt (factor de costo 12 = ~300ms en máquinas modernas)
    salt = bcrypt.gensalt(rounds=12)
    
    # Hashear la contraseña
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Convertir bytes a string para guardar en BD
    return password_hash.decode('utf-8')


def _verificar_password(password: str, password_hash: str) -> bool:
    """
    Verificar que una contraseña coincida con su hash.
    
    Args:
        password (str): Contraseña en texto plano (ingresada por usuario)
        password_hash (str): Hash guardado en la BD
    
    Retorna:
        bool: True si la contraseña es correcta, False caso contrario
    
    Nota:
        bcrypt.checkpw() es timing-safe: tarda siempre lo mismo,
        sin importar dónde falle la comparación (contra timing attacks).
    """
    try:
        # Convertir hash de string a bytes
        password_hash_bytes = password_hash.encode('utf-8')
        
        # Comparar (timing-safe)
        return bcrypt.checkpw(password.encode('utf-8'), password_hash_bytes)
    except Exception:
        # Si hay error (ej: hash corrupto), retornar False
        return False


# ============================================================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================================================

def listar_usuarios_activos() -> list[dict]:
    """
    Listar todos los usuarios activos, para el combo del login.
    
    Retorna:
        list[dict]: Lista de usuarios con estructura {'id': int, 'nombre': str}
    """
    with SessionLocal() as sesion:
        usuarios = sesion.query(Usuario).filter(Usuario.activo == True).all()
        
        resultado = [
            {'id': u.id, 'nombre': u.nombre}
            for u in usuarios
        ]
        
        return resultado


class ResultadoLogin:
    """
    Resultado de un intento de login.
    
    Atributos:
        exitoso (bool): Si el login fue correcto
        mensaje (str): Descripción del resultado
        usuario_id (int | None): ID del usuario si fue exitoso
        necesita_password (bool): Si el usuario no tiene contraseña aún
    """
    
    def __init__(self, exitoso=False, mensaje="", usuario_id=None, necesita_password=False):
        self.exitoso = exitoso
        self.mensaje = mensaje
        self.usuario_id = usuario_id
        self.necesita_password = necesita_password


def verificar_login(usuario_id: int, password: str) -> ResultadoLogin:
    """
    Verificar las credenciales de login.
    
    Args:
        usuario_id (int): ID del usuario (del combo)
        password (str): Contraseña ingresada
    
    Retorna:
        ResultadoLogin: Objeto con resultado y detalles
    
    Casos:
        1. Usuario sin contraseña (primer ingreso): retorna necesita_password=True
        2. Contraseña correcta: retorna exitoso=True
        3. Contraseña incorrecta: retorna exitoso=False
        4. Usuario no existe: retorna exitoso=False
    """
    with SessionLocal() as sesion:
        # Buscar el usuario por ID
        usuario = sesion.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            return ResultadoLogin(
                exitoso=False,
                mensaje="Usuario no encontrado"
            )
        
        # Caso 1: Usuario sin contraseña (primer ingreso)
        if not usuario.password_hash:
            return ResultadoLogin(
                exitoso=False,
                mensaje="Define tu contraseña",
                usuario_id=usuario_id,
                necesita_password=True
            )
        
        # Caso 2 y 3: Verificar contraseña
        if _verificar_password(password, usuario.password_hash):
            return ResultadoLogin(
                exitoso=True,
                mensaje="Login exitoso",
                usuario_id=usuario_id,
                necesita_password=False
            )
        else:
            return ResultadoLogin(
                exitoso=False,
                mensaje="Contraseña incorrecta"
            )


def establecer_password(usuario_id: int, password: str) -> None:
    """
    Establecer la contraseña de un usuario (primer ingreso o admin).
    
    Args:
        usuario_id (int): ID del usuario
        password (str): Contraseña nueva en texto plano
    
    Raises:
        ErrorDeNegocio: Si el usuario no existe
    """
    with SessionLocal() as sesion:
        usuario = sesion.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            raise ErrorDeNegocio(f"Usuario con ID {usuario_id} no existe")
        
        # Hashear y guardar
        usuario.password_hash = _hash_password(password)
        sesion.commit()


def cambiar_password(usuario_id: int, password_actual: str, password_nueva: str) -> None:
    """
    Cambiar la contraseña de un usuario (autoservicio).
    
    Flujo:
    1. Verificar que la contraseña actual sea correcta
    2. Validar que la nueva contraseña sea diferente
    3. Hashear y guardar la nueva contraseña
    
    Args:
        usuario_id (int): ID del usuario
        password_actual (str): Contraseña actual en texto plano
        password_nueva (str): Contraseña nueva en texto plano
    
    Raises:
        ErrorDeNegocio: Si hay validaciones que fallan
    """
    with SessionLocal() as sesion:
        # Buscar el usuario
        usuario = sesion.query(Usuario).filter(Usuario.id == usuario_id).first()
        
        if not usuario:
            raise ErrorDeNegocio("Usuario no encontrado")
        
        # Verificar que la contraseña actual sea correcta
        if not usuario.password_hash:
            raise ErrorDeNegocio(
                "Este usuario no tiene contraseña. "
                "Contacta al administrador."
            )
        
        if not _verificar_password(password_actual, usuario.password_hash):
            raise ErrorDeNegocio("La contraseña actual es incorrecta")
        
        # Verificar que la nueva contraseña sea diferente
        if password_actual == password_nueva:
            raise ErrorDeNegocio(
                "La contraseña nueva debe ser diferente a la actual"
            )
        
        # Hashear y actualizar
        usuario.password_hash = _hash_password(password_nueva)
        sesion.commit()


# ============================================================================
# FUNCIÓN: LISTAR USUARIOS CON SU ESTADO DE CONTRASEÑA (para debugging)
# ============================================================================

def listar_usuarios_con_estado() -> list[dict]:
    """
    Listar todos los usuarios y su estado de contraseña.
    
    Útil para verificar quién ya tiene contraseña y quién no.
    
    Retorna:
        list[dict]: Lista con {'id', 'nombre', 'tiene_password': bool}
    """
    with SessionLocal() as sesion:
        usuarios = sesion.query(Usuario).all()
        
        resultado = [
            {
                'id': u.id,
                'nombre': u.nombre,
                'tiene_password': bool(u.password_hash),
                'activo': u.activo
            }
            for u in usuarios
        ]
        
        return resultado


# ============================================================================
# MAIN (para testing)
# ============================================================================

if __name__ == "__main__":
    """
    Script de debugging: listar usuarios y su estado.
    
    Uso: py -m app.logica.auth
    """
    print("Usuarios en la base de datos:")
    print("=" * 60)
    
    usuarios = listar_usuarios_con_estado()
    for u in usuarios:
        estado = "✓ Con contraseña" if u['tiene_password'] else "✗ Sin contraseña"
        activo = "✓" if u['activo'] else "✗"
        print(f"[{activo}] {u['id']:3d} | {u['nombre']:20s} | {estado}")
    
    print("=" * 60)
    print(f"Total: {len(usuarios)} usuarios")
