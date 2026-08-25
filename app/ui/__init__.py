"""
CASH FLOW AUTOS — Paquete de interfaz gráfica (UI)
==================================================

Este paquete contiene la interfaz gráfica de la aplicación,
construida con PySide6 (Qt para Python).

Módulos:
- main_window: Ventana principal con navegación sidebar
- pantalla_dashboard: Dashboard con saldos en vivo
- pantalla_cobros: Formulario y tabla de cobros
- pantalla_pagos: Formulario y tabla de pagos
- pantalla_reportes: Consultas y exportación de reportes
- componentes: Componentes reutilizables (tarjetas, etc.)
"""

__version__ = "0.1.0"
__author__ = "Cash Flow Autos Team"

from app.ui.main_window import VentanaPrincipal

__all__ = ["VentanaPrincipal"]
