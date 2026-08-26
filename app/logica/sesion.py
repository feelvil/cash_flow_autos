"""
Módulo de sesión: mantiene estado del usuario logueado.

Estructura:
- Variable global con ID y nombre del usuario actual
- Funciones para iniciar/terminar sesión
- Funciones para consultar datos del usuario

Nota: Es un singleton simple. En apps más grandes,
usar un QObject con signals (QApplication.instance() pattern).
"""

# ============================================================================
# ESTADO GLOBAL DE LA SESIÓN
# ============================================================================

# ID del usuario actualmente logueado (None si no hay sesión)
_usuario_id = None

# Nombre del usuario actualmente logueado
_usuario_nombre = None


# ============================================================================
# FUNCIONES DE CONTROL DE SESIÓN
# ============================================================================

def iniciar_sesion(usuario_id: int, usuario_nombre: str) -> None:
    """
    Iniciar la sesión de un usuario tras login exitoso.
    
    Args:
        usuario_id (int): ID del usuario en la BD
        usuario_nombre (str): Nombre del usuario (para mostrar en UI)
    
    Ejemplo:
        >>> iniciar_sesion(5, "Juan Pérez")
        >>> usuario_actual_id()
        5
    """
    global _usuario_id, _usuario_nombre
    
    _usuario_id = usuario_id
    _usuario_nombre = usuario_nombre


def terminar_sesion() -> None:
    """
    Terminar la sesión del usuario actual.
    
    Limpiar el estado global para volver a un estado de "no logueado".
    
    Ejemplo:
        >>> terminar_sesion()
        >>> usuario_actual_id()
        None
    """
    global _usuario_id, _usuario_nombre
    
    _usuario_id = None
    _usuario_nombre = None


# ============================================================================
# FUNCIONES DE CONSULTA
# ============================================================================

def usuario_actual_id() -> int | None:
    """
    Obtener el ID del usuario actualmente logueado.
    
    Retorna:
        int | None: ID del usuario, o None si no hay sesión
    """
    global _usuario_id
    return _usuario_id


def usuario_actual_nombre() -> str | None:
    """
    Obtener el nombre del usuario actualmente logueado.
    
    Retorna:
        str | None: Nombre del usuario, o None si no hay sesión
    """
    global _usuario_nombre
    return _usuario_nombre


def hay_sesion_activa() -> bool:
    """
    Verificar si hay una sesión activa.
    
    Retorna:
        bool: True si hay usuario logueado, False caso contrario
    
    Ejemplo:
        >>> iniciar_sesion(1, "Admin")
        >>> hay_sesion_activa()
        True
        >>> terminar_sesion()
        >>> hay_sesion_activa()
        False
    """
    global _usuario_id
    return _usuario_id is not None


# ============================================================================
# DEBUG
# ============================================================================

if __name__ == "__main__":
    """
    Testing básico del módulo de sesión.
    
    Uso: py -m app.logica.sesion
    """
    print("Testing sesión...")
    print(f"Sesión activa: {hay_sesion_activa()}")
    print(f"Usuario actual: {usuario_actual_nombre()}")
    
    print("\nIniciando sesión...")
    iniciar_sesion(5, "Juan Pérez")
    print(f"Sesión activa: {hay_sesion_activa()}")
    print(f"Usuario actual: {usuario_actual_nombre()} (ID: {usuario_actual_id()})")
    
    print("\nTerminando sesión...")
    terminar_sesion()
    print(f"Sesión activa: {hay_sesion_activa()}")
    print(f"Usuario actual: {usuario_actual_nombre()}")
