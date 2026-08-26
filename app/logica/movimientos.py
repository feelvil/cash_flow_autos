"""
Módulo de movimientos: crear, anular, listar movimientos.

Funciones principales:
- crear_movimiento(): registrar un cobro o pago
- anular_movimiento(): marcar como anulado + crear reversa
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.database.conexion import SessionLocal
from app.database.models import Movimiento, PlanCuentas


class ErrorDeNegocio(Exception):
    """Excepción para errores de validación de negocio."""
    pass


def crear_movimiento(
    sesion: Session,
    *,
    codigo: int,
    fecha: date,
    monto: float,
    usuario_id: int,
    comprobante: Optional[str] = None,
    descripcion: Optional[str] = None,
    periodo_id: Optional[int] = None
) -> Movimiento:
    """
    Crear un nuevo movimiento (cobro o pago).
    
    Args:
        sesion (Session): Sesión de BD (requerida, no crea propia)
        codigo (int): Código del plan de cuentas
        fecha (date): Fecha del movimiento
        monto (float): Monto en pesos (siempre positivo)
        usuario_id (int): ID del usuario que lo carga
        comprobante (str, optional): Número de comprobante
        descripcion (str, optional): Descripción adicional
        periodo_id (int, optional): Período de referencia
    
    Retorna:
        Movimiento: El movimiento creado
    
    Raises:
        ErrorDeNegocio: Si validaciones fallan
    
    Nota:
        El tipo (ingreso/egreso) se determina automáticamente según el
        código / plan de cuentas. Por ahora, asumir que la lógica está
        en el plan de cuentas y derivar de ahí.
    """
    
    # Validar código existe
    plan_cuenta = sesion.query(PlanCuentas).filter(
        PlanCuentas.codigo == codigo
    ).first()
    
    if not plan_cuenta:
        raise ErrorDeNegocio(f"Código {codigo} no existe")
    
    # Validar monto
    if monto <= 0:
        raise ErrorDeNegocio("El monto debe ser mayor a cero")
    
    # Validar fecha
    if fecha > date.today():
        raise ErrorDeNegocio("La fecha no puede ser en el futuro")
    
    # Determinar si es ingreso o egreso según la partida
    # Por simplicidad, asumimos que lo determina la clasificación en plan_cuenta
    # Lógica: si partida es "INGRESOS" → ingresos, sino → egresos
    
    partida = plan_cuenta.partida
    
    es_ingreso = partida.nombre.upper() == "INGRESOS"
    
    # Crear el movimiento
    movimiento = Movimiento(
        fecha=fecha,
        mes=fecha.month,
        plan_cuenta_id=plan_cuenta.id,
        periodo_id=periodo_id,
        comprobante=comprobante,
        ingresos=monto if es_ingreso else 0,
        egresos=monto if not es_ingreso else 0,
        neto=monto if es_ingreso else -monto,
        usuario_id=usuario_id,
        anulado=False,
        descripcion_adicional=descripcion
    )
    
    # Guardar en BD
    sesion.add(movimiento)
    sesion.commit()
    sesion.refresh(movimiento)
    
    return movimiento


def anular_movimiento(
    sesion: Session,
    *,
    movimiento_id: int,
    usuario_id: int,
    descripcion_reversa: Optional[str] = None
) -> Movimiento:
    """
    Anular un movimiento y crear su reversa automáticamente.
    
    Flujo:
    1. Validar que el movimiento existe y no está ya anulado
    2. Marcar original como anulado
    3. Crear movimiento inverso (reversa)
    4. Linkear: original.movimiento_anulacion_id = reversa.id
    
    Args:
        sesion (Session): Sesión de BD
        movimiento_id (int): ID del movimiento a anular
        usuario_id (int): ID del usuario que anula
        descripcion_reversa (str, optional): Descripción de la anulación
    
    Retorna:
        Movimiento: El movimiento reversa creado
    
    Raises:
        ErrorDeNegocio: Si validaciones fallan
    """
    
    # Buscar el movimiento original
    original = sesion.query(Movimiento).filter(
        Movimiento.id == movimiento_id
    ).first()
    
    if not original:
        raise ErrorDeNegocio(f"Movimiento {movimiento_id} no existe")
    
    if original.anulado:
        raise ErrorDeNegocio("El movimiento ya está anulado")
    
    # Crear la reversa (montos invertidos)
    reversa = Movimiento(
        fecha=original.fecha,
        mes=original.mes,
        plan_cuenta_id=original.plan_cuenta_id,
        periodo_id=original.periodo_id,
        comprobante=original.comprobante,
        ingresos=original.egresos,  # Invertir
        egresos=original.ingresos,  # Invertir
        neto=-original.neto,        # Invertir
        usuario_id=usuario_id,
        anulado=False,
        movimiento_anulacion_id=None,  # La reversa no se anula
        descripcion_adicional=descripcion_reversa or f"Reversa de movimiento {original.id}"
    )
    
    # Guardar reversa
    sesion.add(reversa)
    sesion.flush()  # Para obtener el ID de la reversa
    
    # Marcar original como anulado y linkear
    original.anulado = True
    original.movimiento_anulacion_id = reversa.id
    
    # Guardar cambios
    sesion.commit()
    sesion.refresh(reversa)
    
    return reversa


def listar_movimientos_por_usuario(
    usuario_id: int,
    sesion: Optional[Session] = None
) -> list:
    """
    Listar todos los movimientos cargados por un usuario.
    
    Args:
        usuario_id (int): ID del usuario
        sesion (Session, optional): Sesión de BD
    
    Retorna:
        list: Movimientos cargados por ese usuario
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        movimientos = sesion.query(Movimiento).filter(
            Movimiento.usuario_id == usuario_id
        ).order_by(
            Movimiento.fecha.desc()
        ).all()
        
        return movimientos
    
    finally:
        if usar_sesion_propia:
            sesion.close()


if __name__ == "__main__":
    """Testing: crear movimiento."""
    from app.database.conexion import SessionLocal
    
    print("Testing crear movimiento...")
    
    with SessionLocal() as sesion:
        try:
            # Crear un movimiento de prueba
            mov = crear_movimiento(
                sesion,
                codigo=1041131,
                fecha=date.today(),
                monto=1000.0,
                usuario_id=1,
                comprobante="TEST-001"
            )
            print(f"✓ Movimiento creado: ID {mov.id}, ${mov.neto:,.2f}")
        
        except ErrorDeNegocio as e:
            print(f"✗ Error: {e}")
