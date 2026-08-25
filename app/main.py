"""
CASH FLOW AUTOS — Punto de entrada principal
============================================

Script principal para ejecutar la aplicación:
    python app/main.py

Si se usa PyInstaller, esto se compila a:
    CashFlowAutos.exe
"""

import sys
from pathlib import Path

# Agregar la raíz del proyecto al path para importaciones relativas
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.ui.main_window import VentanaPrincipal


def configurar_aplicacion():
    """
    Configura parámetros globales de la aplicación.
    """
    # Configurar interpolación de pantalla (importante en pantallas 4K)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def main():
    """
    Función principal que lanza la aplicación.
    """
    # Crear la aplicación Qt
    app = QApplication(sys.argv)
    
    # Configurar
    configurar_aplicacion()
    
    # Crear y mostrar la ventana principal
    ventana_principal = VentanaPrincipal()
    ventana_principal.show()
    
    # Navegar al dashboard por defecto
    ventana_principal._cambiar_pantalla("dashboard")
    
    # Ejecutar el loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
