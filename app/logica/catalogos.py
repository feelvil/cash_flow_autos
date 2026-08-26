"""
Módulo de catálogos: obtener listas de códigos, partidas, sub-partidas, etc.

Funciones para poblar combos y hacer búsquedas.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.database.conexion import SessionLocal
from app.database.models import (
    PlanCuentas, Partida, SubPartida, Detalle, Automotriz, Periodo
)


def listar_codigos_con_detalle(sesion: Optional[Session] = None) -> List[Dict]:
    """
    Listar todos los códigos de plan de cuentas con su clasificación.
    
    Retorna:
        List[Dict]: Lista de códigos con estructura:
        {
            'codigo': int,
            'partida': str,
            'tipo_operacion': str,
            'sub_partida': str,
            'detalle': str,
            'automotriz': str (o None),
            'descripcion': str (concatenado para UI)
        }
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        # Consultar todos los planes de cuentas activos
        codigos = sesion.query(
            PlanCuentas.codigo,
            Partida.nombre.label('partida'),
            SubPartida.nombre.label('sub_partida'),
            Detalle.nombre.label('detalle'),
            Automotriz.nombre.label('automotriz')
        ).join(
            Partida, PlanCuentas.partida_id == Partida.id
        ).join(
            SubPartida, PlanCuentas.sub_partida_id == SubPartida.id
        ).join(
            Detalle, PlanCuentas.detalle_id == Detalle.id
        ).outerjoin(
            Automotriz, PlanCuentas.automotriz_id == Automotriz.id
        ).filter(
            PlanCuentas.activo == True
        ).all()
        
        resultado = []
        for cod in codigos:
            # Armar descripción legible
            desc_partes = [cod.sub_partida, cod.detalle]
            if cod.automotriz:
                desc_partes.append(f"({cod.automotriz})")
            
            descripcion = " - ".join(desc_partes)
            
            resultado.append({
                'codigo': cod.codigo,
                'partida': cod.partida,
                'sub_partida': cod.sub_partida,
                'detalle': cod.detalle,
                'automotriz': cod.automotriz,
                'descripcion': descripcion
            })
        
        return resultado
    
    finally:
        if usar_sesion_propia:
            sesion.close()


def buscar_codigo_por_nombre(
    palabras: str,
    sesion: Optional[Session] = None
) -> List[Dict]:
    """
    Buscar códigos por palabras clave (sin acentos, case-insensitive).
    
    Args:
        palabras (str): Palabras a buscar, separadas por espacios
                        Ej: "cordoba vw"
        sesion (Session, optional): Sesión de BD
    
    Retorna:
        List[Dict]: Códigos que coinciden
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        # Obtener todos los códigos
        codigos = listar_codigos_con_detalle(sesion)
        
        # Normalizar palabras de búsqueda
        palabras_norm = [p.lower() for p in palabras.split()]
        
        # Filtrar: todos los códigos que contienen TODAS las palabras
        resultado = []
        for cod in codigos:
            # Armar texto combinado para buscar
            texto_busqueda = (
                f"{cod['codigo']} {cod['sub_partida']} {cod['detalle']} "
                f"{cod.get('automotriz', '')}"
            ).lower()
            
            # Verificar que todas las palabras están en el texto
            if all(palabra in texto_busqueda for palabra in palabras_norm):
                resultado.append(cod)
        
        return resultado
    
    finally:
        if usar_sesion_propia:
            sesion.close()


def obtener_codigo_por_numero(codigo: int, sesion: Optional[Session] = None) -> Optional[Dict]:
    """
    Obtener un código específico por su número.
    
    Args:
        codigo (int): Número del código a buscar
        sesion (Session, optional): Sesión de BD
    
    Retorna:
        Dict: Información del código, o None si no existe
    """
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        codigos = listar_codigos_con_detalle(sesion)
        
        for cod in codigos:
            if cod['codigo'] == codigo:
                return cod
        
        return None
    
    finally:
        if usar_sesion_propia:
            sesion.close()


def listar_partidas(sesion: Optional[Session] = None) -> List[Dict]:
    """Listar todas las partidas activas."""
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        partidas = sesion.query(
            Partida.id, Partida.nombre
        ).filter(
            Partida.activa == True
        ).all()
        
        return [{'id': p.id, 'nombre': p.nombre} for p in partidas]
    
    finally:
        if usar_sesion_propia:
            sesion.close()


def listar_sub_partidas(sesion: Optional[Session] = None) -> List[Dict]:
    """Listar todas las sub-partidas activas."""
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        sub_partidas = sesion.query(
            SubPartida.id, SubPartida.nombre
        ).filter(
            SubPartida.activa == True
        ).all()
        
        return [{'id': sp.id, 'nombre': sp.nombre} for sp in sub_partidas]
    
    finally:
        if usar_sesion_propia:
            sesion.close()


def listar_automotrices(sesion: Optional[Session] = None) -> List[Dict]:
    """Listar todos los grupos automotrices activos."""
    usar_sesion_propia = False
    
    if sesion is None:
        sesion = SessionLocal()
        usar_sesion_propia = True
    
    try:
        autos = sesion.query(
            Automotriz.id, Automotriz.codigo, Automotriz.nombre
        ).filter(
            Automotriz.activo == True
        ).all()
        
        return [
            {'id': a.id, 'codigo': a.codigo, 'nombre': a.nombre}
            for a in autos
        ]
    
    finally:
        if usar_sesion_propia:
            sesion.close()


if __name__ == "__main__":
    """Testing: listar códigos."""
    print("Códigos disponibles:")
    codigos = listar_codigos_con_detalle()
    for cod in codigos[:10]:  # Primeros 10
        print(f"  {cod['codigo']:7d} | {cod['descripcion']}")
    print(f"\nTotal: {len(codigos)} códigos")
    
    print("\nBúsqueda: 'cordoba vw'")
    resultados = buscar_codigo_por_nombre("cordoba vw")
    for cod in resultados:
        print(f"  {cod['codigo']:7d} | {cod['descripcion']}")
