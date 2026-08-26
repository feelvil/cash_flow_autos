"""
CASH FLOW AUTOS — Punto de entrada principal
============================================

Script principal para ejecutar la aplicación:
    python app/main.py

Flujo de arranque:
    1. Se muestra la ventana de LOGIN.
    2. Si el login es exitoso, se guarda el usuario en sesión y arranca la app.
    3. Si se cancela el login, la app no abre.

Si se usa PyInstaller, esto se compila a:
    CashFlowAutos.exe
"""

import sys
from pathlib import Path

# Agregar la raíz del proyecto al path para importaciones relativas
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt
from app.ui.main_window import VentanaPrincipal
from app.ui.ventana_login import VentanaLogin
from app.logica import sesion


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

    # ═════════════════════════════════════════════════════
    # 1. LOGIN — se muestra antes que nada.
    # ═════════════════════════════════════════════════════
    login = VentanaLogin()
    if login.exec() != QDialog.DialogCode.Accepted:
        # El usuario cerró el login sin ingresar: no abrimos la app.
        sys.exit(0)

    # Guardar el usuario logueado en la sesión global. Desde acá, las pantallas
    # de carga usan sesion.usuario_actual_id() en vez del viejo usuario_id=1.
    sesion.iniciar_sesion(login.usuario_id, login.usuario_nombre)

    # ═════════════════════════════════════════════════════
    # 2. APP PRINCIPAL
    # ═════════════════════════════════════════════════════
    ventana_principal = VentanaPrincipal()
    ventana_principal.show()

    # Navegar al dashboard por defecto
    ventana_principal._cambiar_pantalla("dashboard")

    # Ejecutar el loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
