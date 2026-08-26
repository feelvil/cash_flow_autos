"""
Módulo de saldos: cálculo de saldos totales, por período, por categoría, etc.

Funciones principales:
- calcular_saldo_total(): saldo general actual
- calcular_saldo_por_automotriz(): saldo por grupo automotriz
- calcular_saldo_por_periodo(): saldo por período
- movimientos_detallados(): consulta filtrada de movimientos con JOIN a clasificaciones
"""

from datetime import datetime, date
from typing import List, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database.conexion import SessionLocal
from app.database.models import (
    Movimiento, PlanCuentas, Partida, SubPartida, Detalle, 
    Automotriz, Periodo, Usuario
)


# ============================================================================
# FUNCIONES PRINCIPALES DE CÁLCULO
# ============================================================================

def calcular_saldo_total(sesion: Optional[Session] = None) -> float:
    """
    Calcular el saldo total actual (suma de todos los movimientos no anulados).
    
    Args:
        sesion (Session, optional): Sesión de BD. Si no se proporciona, crea una.
    
    Retorna:
        float: Saldo total en pesos
    
    Fórmula:
        Saldo = SUM(ingresos - egresos) WHERE anulado = false
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        # Sumar ingresos menos egresos de todos los movimientos activos
        resultado = sesion.query(
            func.sum(Movimiento.ingresos - Movimiento.egresos)
        ).filter(Movimiento.anulado == False).scalar()
        
        # Si no hay movimientos, retornar 0
        saldo_total = resultado if resultado is not None else 0.0
        
        return float(saldo_total)
    
    finally:
        if usar_sesion_propia:
            sesion.close()


def calcular_saldo_por_automotriz(sesion: Optional[Session] = None) -> Dict[str, float]:
    """
    Calcular el saldo por grupo automotriz (VW, Plan Rombo, etc.).
    
    Args:
        sesion (Session, optional): Sesión de BD
    
    Retorna:
        Dict[str, float]: Mapeo {nombre_automotriz: saldo_total}
    
    Nota:
        Los movimientos transversales (automotriz_id = NULL) se incluyen bajo
        una clave especial: "(Transversal)"
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        # Agrupar por automotriz (incluyendo NULL)
        resultados = sesion.query(
            Automotriz.nombre,
            func.sum(Movimiento.ingresos - Movimiento.egresos)
        ).outerjoin(
            PlanCuentas, PlanCuentas.automotriz_id == Automotriz.id
        ).outerjoin(
            Movimiento, Movimiento.plan_cuenta_id == PlanCuentas.id
        ).filter(
            Movimiento.anulado == False
        ).group_by(
            Automotriz.nombre
        ).all()
        
        saldos = {}
        for nombre, saldo in resultados:
            if nombre:
                saldos[nombre] = float(saldo) if saldo else 0.0
        
        # Calcular movimientos transversales (automotriz_id = NULL)
        saldo_transversal = sesion.query(
            func.sum(Movimiento.ingresos - Movimiento.egresos)
        ).join(
            PlanCuentas, Movimiento.plan_cuenta_id == PlanCuentas.id
        ).filter(
            and_(
                Movimiento.anulado == False,
                PlanCuentas.automotriz_id == None
            )
        ).scalar()
        
        if saldo_transversal:
            saldos["(Transversal)"] = float(saldo_transversal)
        
        return saldos
    
    finally:
        if usar_sesion_propia:
            sesion.close()


def calcular_saldo_por_periodo(sesion: Optional[Session] = None) -> Dict[str, float]:
    """
    Calcular el saldo por período contable.
    
    Args:
        sesion (Session, optional): Sesión de BD
    
    Retorna:
        Dict[str, float]: Mapeo {año-mes: saldo_total}
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        # Agrupar por período
        resultados = sesion.query(
            Periodo.descripcion,
            func.sum(Movimiento.ingresos - Movimiento.egresos)
        ).outerjoin(
            Periodo, Movimiento.periodo_id == Periodo.id
        ).filter(
            Movimiento.anulado == False
        ).group_by(
            Periodo.descripcion
        ).all()
        
        saldos = {}
        for descripcion, saldo in resultados:
            clave = descripcion if descripcion else "(Sin período)"
            saldos[clave] = float(saldo) if saldo else 0.0
        
        return saldos
    
    finally:
        if usar_sesion_propia:
            sesion.close()


# ============================================================================
# FUNCIONES DE CONSULTA DETALLADA
# ============================================================================

def movimientos_detallados(
    sesion: Optional[Session] = None,
    *,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    codigo: Optional[int] = None,
    sub_partida_id: Optional[int] = None,
    automotriz_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    solo_activos: bool = True,
    limite: int = 1000,
    ordenar_descendente: bool = False
) -> List[Dict]:
    """
    Consultar movimientos con JOIN a todas sus clasificaciones.
    
    Args:
        sesion (Session, optional): Sesión de BD
        fecha_inicio (date, optional): Filtro por fecha mínima
        fecha_fin (date, optional): Filtro por fecha máxima
        codigo (int, optional): Filtro por código de plan de cuentas
        sub_partida_id (int, optional): Filtro por sub-partida
        automotriz_id (int, optional): Filtro por automotriz
        usuario_id (int, optional): Filtro por usuario que lo cargó
        solo_activos (bool): Si True, excluir movimientos anulados
        limite (int): Máximo de filas a retornar
        ordenar_descendente (bool): Si True, ordenar por fecha DESC
    
    Retorna:
        List[Dict]: Lista de movimientos con toda su clasificación
        
        Cada dict contiene:
        {
            'id': int,
            'fecha': date,
            'mes': int,
            'codigo': int,
            'comprobante': str,
            'ingresos': float,
            'egresos': float,
            'neto': float,
            'partida': str,
            'tipo_operacion': str,
            'sub_partida': str,
            'detalle': str,
            'automotriz': str (o None),
            'usuario': str,
            'anulado': bool,
            'creado_en': datetime
        }
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        # Construir query base
        query = sesion.query(
            Movimiento.id,
            Movimiento.fecha,
            Movimiento.mes,
            PlanCuentas.codigo,
            Movimiento.comprobante,
            Movimiento.ingresos,
            Movimiento.egresos,
            (Movimiento.ingresos - Movimiento.egresos).label('neto'),
            Partida.nombre.label('partida'),
            # TiposOperacion.nombre.label('tipo_operacion'),
            SubPartida.nombre.label('sub_partida'),
            Detalle.nombre.label('detalle'),
            Automotriz.nombre.label('automotriz'),
            Usuario.nombre.label('usuario'),
            Movimiento.anulado,
            Movimiento.creado_en
        ).join(
            PlanCuentas, Movimiento.plan_cuenta_id == PlanCuentas.id
        ).join(
            Partida, PlanCuentas.partida_id == Partida.id
        ).join(
            SubPartida, PlanCuentas.sub_partida_id == SubPartida.id
        ).join(
            Detalle, PlanCuentas.detalle_id == Detalle.id
        ).outerjoin(
            Automotriz, PlanCuentas.automotriz_id == Automotriz.id
        ).join(
            Usuario, Movimiento.usuario_id == Usuario.id
        )
        
        # Aplicar filtros
        if solo_activos:
            query = query.filter(Movimiento.anulado == False)
        
        if fecha_inicio:
            query = query.filter(Movimiento.fecha >= fecha_inicio)
        
        if fecha_fin:
            query = query.filter(Movimiento.fecha <= fecha_fin)
        
        if codigo:
            query = query.filter(PlanCuentas.codigo == codigo)
        
        if sub_partida_id:
            query = query.filter(PlanCuentas.sub_partida_id == sub_partida_id)
        
        if automotriz_id:
            query = query.filter(PlanCuentas.automotriz_id == automotriz_id)
        
        if usuario_id:
            query = query.filter(Movimiento.usuario_id == usuario_id)
        
        # Ordenar
        if ordenar_descendente:
            query = query.order_by(Movimiento.fecha.desc(), Movimiento.id.desc())
        else:
            query = query.order_by(Movimiento.fecha.asc(), Movimiento.id.asc())
        
        # Aplicar límite
        query = query.limit(limite)
        
        # Ejecutar y convertir a dicts
        resultados = []
        for row in query.all():
            resultados.append({
                'id': row.id,
                'fecha': row.fecha,
                'mes': row.mes,
                'codigo': row.codigo,
                'comprobante': row.comprobante,
                'ingresos': float(row.ingresos),
                'egresos': float(row.egresos),
                'neto': float(row.neto),
                'partida': row.partida,
                # 'tipo_operacion': row.tipo_operacion,
                'sub_partida': row.sub_partida,
                'detalle': row.detalle,
                'automotriz': row.automotriz,
                'usuario': row.usuario,
                'anulado': row.anulado,
                'creado_en': row.creado_en
            })
        
        return resultados
    
    finally:
        if usar_sesion_propia:
            sesion.close()


# ============================================================================
# DEBUG / TESTING
# ============================================================================

if __name__ == "__main__":
    """
    Script de testing: calcular saldos contra la BD real.
    
    Uso: py -m app.logica.saldos
    """
    print("Cálculo de saldos desde BD...")
    print("=" * 60)
    
    # Saldo total
    saldo_total = calcular_saldo_total()
    print(f"Saldo total: ${saldo_total:,.2f}")
    
    # Saldo por automotriz
    print("\nSaldo por automotriz:")
    saldos_auto = calcular_saldo_por_automotriz()
    for auto, saldo in sorted(saldos_auto.items()):
        print(f"  {auto:30s}: ${saldo:>15,.2f}")
    
    # Últimos 5 movimientos
    print("\nÚltimos 5 movimientos:")
    movs = movimientos_detallados(limite=5, ordenar_descendente=True)
    for mov in movs:
        print(
            f"  {mov['fecha']} | {mov['codigo']:7d} | "
            f"{mov['sub_partida']:20s} | ${mov['neto']:>12,.2f}"
        )
    
    print("=" * 60)
