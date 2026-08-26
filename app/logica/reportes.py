"""
Módulo de reportes: generar reportes por período, categoría, etc.

Funciones para armar reportes que se exportan a Excel.
"""

from datetime import date
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from app.database.conexion import SessionLocal
from app.logica.saldos import movimientos_detallados


def reporte_por_periodo(
    fecha_inicio: date,
    fecha_fin: date,
    sesion: Optional[Session] = None
) -> Dict:
    """
    Generar reporte de movimientos en un período.
    
    Args:
        fecha_inicio (date): Fecha inicial
        fecha_fin (date): Fecha final
        sesion (Session, optional): Sesión de BD
    
    Retorna:
        Dict con estructura:
        {
            'periodo': str (ej: "01/01/2026 - 31/01/2026"),
            'movimientos': list,
            'totales': {
                'ingresos_total': float,
                'egresos_total': float,
                'neto_total': float
            }
        }
    """
    
    # Obtener movimientos en el período
    movimientos = movimientos_detallados(
        sesion=sesion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        solo_activos=True
    )
    
    # Calcular totales
    totales = {
        'ingresos_total': sum(m['ingresos'] for m in movimientos),
        'egresos_total': sum(m['egresos'] for m in movimientos),
        'neto_total': sum(m['neto'] for m in movimientos)
    }
    
    return {
        'periodo': f"{fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}",
        'movimientos': movimientos,
        'totales': totales
    }


def reporte_por_sub_partida(
    sesion: Optional[Session] = None
) -> List[Dict]:
    """
    Generar reporte agrupado por sub-partida.
    
    Retorna:
        List[Dict]:
        [{
            'sub_partida': str,
            'movimientos': list,
            'total': float
        }, ...]
    """
    
    # Obtener todos los movimientos
    movimientos = movimientos_detallados(sesion=sesion, solo_activos=True)
    
    # Agrupar por sub-partida
    grupos = {}
    for mov in movimientos:
        sp = mov['sub_partida']
        if sp not in grupos:
            grupos[sp] = []
        grupos[sp].append(mov)
    
    # Armar resultado
    resultado = []
    for sub_partida, movs in sorted(grupos.items()):
        total = sum(m['neto'] for m in movs)
        resultado.append({
            'sub_partida': sub_partida,
            'movimientos': movs,
            'total': total,
            'cantidad': len(movs)
        })
    
    return resultado


def reporte_por_automotriz(
    sesion: Optional[Session] = None
) -> List[Dict]:
    """
    Generar reporte agrupado por automotriz.
    
    Retorna:
        List[Dict]:
        [{
            'automotriz': str,
            'movimientos': list,
            'total': float
        }, ...]
    """
    
    # Obtener todos los movimientos
    movimientos = movimientos_detallados(sesion=sesion, solo_activos=True)
    
    # Agrupar por automotriz
    grupos = {}
    for mov in movimientos:
        auto = mov['automotriz'] or "(Transversal)"
        if auto not in grupos:
            grupos[auto] = []
        grupos[auto].append(mov)
    
    # Armar resultado
    resultado = []
    for automotriz, movs in sorted(grupos.items()):
        total = sum(m['neto'] for m in movs)
        resultado.append({
            'automotriz': automotriz,
            'movimientos': movs,
            'total': total,
            'cantidad': len(movs)
        })
    
    return resultado


def generar_reporte_excel(
    fecha_inicio: date,
    fecha_fin: date,
    sesion: Optional[Session] = None
) -> str:
    """
    Placeholder: generar archivo Excel con reporte.
    
    En v1.1 se implementa usando openpyxl.
    
    Args:
        fecha_inicio (date): Período inicio
        fecha_fin (date): Período fin
        sesion (Session, optional): Sesión de BD
    
    Retorna:
        str: Ruta del archivo generado
    """
    # TODO: Implementar con openpyxl
    return "reporte_pendiente.xlsx"


if __name__ == "__main__":
    """Testing: generar reportes."""
    from datetime import timedelta
    
    print("Testing reportes...")
    
    hoy = date.today()
    inicio = hoy - timedelta(days=30)
    
    print(f"\nReporte período {inicio} a {hoy}")
    reporte = reporte_por_periodo(inicio, hoy)
    print(f"  Movimientos: {len(reporte['movimientos'])}")
    print(f"  Ingresos: ${reporte['totales']['ingresos_total']:,.2f}")
    print(f"  Egresos: ${reporte['totales']['egresos_total']:,.2f}")
    print(f"  Neto: ${reporte['totales']['neto_total']:,.2f}")
    
    print("\nReporte por sub-partida")
    sub_partidas = reporte_por_sub_partida()
    for sp in sub_partidas[:5]:  # Primeras 5
        print(f"  {sp['sub_partida']:30s}: ${sp['total']:>12,.2f} ({sp['cantidad']} movs)")
