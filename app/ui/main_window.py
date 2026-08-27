"""
Ventana principal de Cash Flow Autos.

Estructura:
- Sidebar con navegación: Dashboard, Cobros, Pagos, Reportes, Opciones
- Panel principal que cambia según la opción seleccionada
- Header con nombre del usuario logueado
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

# Importar las pantallas específicas
from app.ui.panel_dashboard import PanelDashboard
from app.ui.pantalla_cobros import PantallaCobros
from app.ui.pantalla_pagos import PantallaPagos
from app.ui.pantalla_reportes import PantallarePortes  # Nota: nombre de clase es PantallarePortes
from app.ui.panel_opciones import PanelOpciones

# Importar sesión para obtener el usuario actual
from app.logica import sesion


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la aplicación.
    
    Maneja:
    - Navegación mediante sidebar
    - Visualización del panel activo (stacked widget)
    - Header con información del usuario
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuración básica
        self.setWindowTitle("Cash Flow Autos")
        self.setGeometry(100, 100, 1400, 800)
        
        # Crear widget central y layout principal
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        
        # ========================================================================
        # SIDEBAR (navegación)
        # ========================================================================
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(180)
        self.sidebar.setMinimumWidth(180)
        
        # Definir opciones de navegación (sin Categorías ni Cuentas)
        opciones_nav = [
            ("Dashboard", "ti-layout-dashboard"),
            ("Cobros", "ti-arrow-down-left"),
            ("Pagos", "ti-arrow-up-right"),
            ("Reportes", "ti-chart-bar"),
            ("Opciones", "ti-settings"),
        ]
        
        # Agregar cada opción al sidebar
        for texto, icono in opciones_nav:
            item = QListWidgetItem(texto)
            item.setIcon(QIcon())  # Placeholder para ícono (PySide6 + Tabler)
            item.setSizeHint(QSize(180, 50))
            self.sidebar.addItem(item)
        
        # Conectar cambios de selección del sidebar
        self.sidebar.itemClicked.connect(self._cambiar_panel)
        
        # ========================================================================
        # AREA PRINCIPAL (stacked widget para cambiar paneles)
        # ========================================================================
        self.paneles = QStackedWidget()
        
        # Crear cada panel
        self.panel_dashboard = PanelDashboard()
        self.panel_cobros = PantallaCobros()
        self.panel_pagos = PantallaPagos()
        self.panel_reportes = PantallarePortes()
        self.panel_opciones = PanelOpciones()
        
        # Agregar paneles al stacked widget
        self.paneles.addWidget(self.panel_dashboard)  # índice 0
        self.paneles.addWidget(self.panel_cobros)      # índice 1
        self.paneles.addWidget(self.panel_pagos)       # índice 2
        self.paneles.addWidget(self.panel_reportes)    # índice 3
        self.paneles.addWidget(self.panel_opciones)    # índice 4
        
        # ========================================================================
        # HEADER (información del usuario y botón cerrar sesión)
        # ========================================================================
        header = self._crear_header()
        
        # ========================================================================
        # Armar layout final
        # ========================================================================
        layout_derecha = QVBoxLayout()
        layout_derecha.setContentsMargins(0, 0, 0, 0)
        layout_derecha.setSpacing(0)
        layout_derecha.addWidget(header)
        layout_derecha.addWidget(self.paneles)
        
        layout_principal.addWidget(self.sidebar)
        layout_principal.addLayout(layout_derecha)
        
        # Mostrar primer panel por defecto
        self.paneles.setCurrentIndex(0)
        self.sidebar.setCurrentRow(0)
    
    def _crear_header(self):
        """
        Crear el header con información del usuario.
        
        Muestra:
        - Nombre del usuario logueado
        - Botón "Cerrar sesión"
        """
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        # Obtener nombre del usuario actual
        nombre_usuario = sesion.usuario_actual_nombre()
        
        # Label con el nombre
        label_usuario = QLabel(f"Conectado como: {nombre_usuario}")
        label_usuario.setStyleSheet("font-size: 13px; color: #666;")
        
        # Botón cerrar sesión (spacer a la derecha)
        btn_cerrar = QPushButton("Cerrar sesión")
        btn_cerrar.setMaximumWidth(120)
        btn_cerrar.clicked.connect(self._cerrar_sesion)
        
        # Armar header
        header_layout.addWidget(label_usuario)
        header_layout.addStretch()
        header_layout.addWidget(btn_cerrar)
        
        header_widget.setStyleSheet(
            "background-color: #f5f5f5; border-bottom: 1px solid #ddd;"
        )
        header_widget.setMaximumHeight(40)
        
        return header_widget
    
    def _cambiar_panel(self, item):
        """
        Cambiar el panel activo según la opción seleccionada en el sidebar.
        
        Args:
            item (QListWidgetItem): El item seleccionado en el sidebar
        """
        # Obtener el índice del item en la lista
        indice = self.sidebar.row(item)
        
        # Cambiar al panel correspondiente
        self.paneles.setCurrentIndex(indice)
    
    def _cerrar_sesion(self):
        """
        Cerrar la sesión del usuario actual y volver a la pantalla de login.
        
        Nota: En v1, esto cierra la app. En v2, se podría volver a mostrar
        el login sin cerrar la ventana.
        """
        # Terminar la sesión actual
        sesion.terminar_sesion()
        
        # Cerrar la app
        self.close()
