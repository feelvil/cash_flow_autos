"""
sesion.py
=========
Guarda quién es el usuario logueado, para que cualquier pantalla lo consulte
sin tener que pasarlo por parámetro por toda la cadena de constructores.

Es un módulo simple con estado a nivel de módulo (una especie de "singleton"):
después del login, main.py llama a iniciar_sesion(id, nombre), y desde ahí
cualquier pantalla usa usuario_actual_id() al guardar un movimiento.

Antes de esto, Cobros y Pagos usaban un usuario_id=1 fijo. Ahora usan el real.
"""

# Estado del usuario logueado (privado del módulo).
_usuario_id: int | None = None
_usuario_nombre: str | None = None


def iniciar_sesion(usuario_id: int, nombre: str) -> None:
    """Registra al usuario que acaba de loguearse. Lo llama main.py tras el login."""
    global _usuario_id, _usuario_nombre
    _usuario_id = usuario_id
    _usuario_nombre = nombre


def cerrar_sesion() -> None:
    """Limpia la sesión (para un futuro 'cerrar sesión' desde la app)."""
    global _usuario_id, _usuario_nombre
    _usuario_id = None
    _usuario_nombre = None


def usuario_actual_id() -> int:
    """
    Devuelve el id del usuario logueado. Si por algún motivo no hay sesión
    (no debería pasar si el login corrió primero), cae a 1 (Sistema) como
    respaldo seguro, para que la carga de movimientos nunca quede sin usuario.
    """
    return _usuario_id if _usuario_id is not None else 1


def usuario_actual_nombre() -> str:
    """Devuelve el nombre del usuario logueado (o 'Sistema' si no hay sesión)."""
    return _usuario_nombre if _usuario_nombre is not None else "Sistema"


def hay_sesion() -> bool:
    """True si hay un usuario logueado."""
    return _usuario_id is not None
