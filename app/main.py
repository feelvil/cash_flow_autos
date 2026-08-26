"""
Punto de entrada de Cash Flow Autos.

Flujo:
1. Crear aplicación QApplication
2. Mostrar pantalla de login
3. Si login exitoso, mostrar ventana principal
4. Ejecutar event loop
"""

import sys
from pathlib import Path

# Agregar raíz del proyecto al path ANTES de importar app
# Esto permite que los imports funcionen sin importar dónde se ejecute el script
project_root = Path(__file__).parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication

# Importar las pantallas
from app.ui.ventana_login import VentanaLogin


def main():
    """
    Función principal: inicializar la app y mostrar login.
    """
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    
    # Mostrar ventana de login
    ventana_login = VentanaLogin()
    ventana_login.show()
    
    # Ejecutar event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

