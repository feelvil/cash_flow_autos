"""
CASH FLOW AUTOS — Ventana Principal
====================================

Gestiona la interfaz principal de la aplicación:
- Sidebar izquierdo con navegación
- Panel central que cambia según la sección seleccionada
- Header con información del usuario

Patrón de diseño: Cada pantalla (Dashboard, Cobros, etc.) es un widget
separado que se intercambia en el QStackedWidget central.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
import os

# Importar las pantallas (se hacen lazy para que carguen rápido)
# Por ahora están vacías, se crean después


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal de la aplicación.
    
    Layout general:
    ┌─────────────────────────────────────────────┐
    │ HEADER (Usuario, hora, opciones)            │
    ├──────────────┬──────────────────────────────┤
    │              │                              │
    │   SIDEBAR    │     PANEL CENTRAL            │
    │ (Navegación) │   (QStackedWidget que        │
    │              │    alterna pantallas)        │
    │              │                              │
    └──────────────┴──────────────────────────────┘
    """
    
    def __init__(self):
        """Inicializa la ventana principal."""
        super().__init__()
        
        # Propiedades de la ventana
        self.setWindowTitle("Cash Flow Autos — Gestión de Flujo de Fondos")
        self.setWindowIcon(self._crear_icono())
        self.setMinimumSize(1200, 700)
        
        # Referencias a las pantallas (se cargan bajo demanda)
        self.pantallas = {}
        
        # Crear la interfaz
        self._crear_ui()
        self._cargar_estilos()
        
        # Conectar señales
        self._conectar_senales()
    
    def _crear_ui(self):
        """Crea la interfaz de usuario (layout principal)."""
        
        # Widget central que contiene todo
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        
        # Layout principal (horizontal): sidebar + contenido
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)  # Sin márgenes
        layout_principal.setSpacing(0)  # Sin espacios
        
        # ═════════════════════════════════════════════════════
        # SIDEBAR (Navegación izquierda)
        # ═════════════════════════════════════════════════════
        self.sidebar = self._crear_sidebar()
        layout_principal.addWidget(self.sidebar)
        
        # ═════════════════════════════════════════════════════
        # PANEL CENTRAL CON HEADER + STACKED WIDGET
        # ═════════════════════════════════════════════════════
        widget_derecha = QWidget()
        layout_derecha = QVBoxLayout(widget_derecha)
        layout_derecha.setContentsMargins(0, 0, 0, 0)
        layout_derecha.setSpacing(0)
        
        # Header (información del usuario, hora, opciones)
        header = self._crear_header()
        layout_derecha.addWidget(header)
        
        # Panel central intercambiable (QStackedWidget)
        self.stack_contenido = QStackedWidget()
        layout_derecha.addWidget(self.stack_contenido)
        
        layout_principal.addWidget(widget_derecha, 1)  # Tomar todo el espacio
        
        # Ajustar proporción sidebar:contenido (230px : resto)
        layout_principal.setStretch(0, 0)  # Sidebar fijo
        layout_principal.setStretch(1, 1)  # Contenido flexible
    
    def _crear_sidebar(self) -> QFrame:
        """
        Crea el sidebar izquierdo con navegación.
        
        Retorna:
            QFrame con botones de navegación y logo
        """
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Logo y nombre de la app
        logo_layout = QVBoxLayout()
        logo_label = QLabel("📊 Cash Flow")
        logo_label.setObjectName("logoLabel")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        logo_layout.addWidget(separador)
        
        layout.addLayout(logo_layout)
        
        # Botones de navegación
        self.botones_nav = {}
        
        # Orden de navegación: nombre_id, etiqueta, icono
        items_nav = [
            ("dashboard", "📈 Dashboard", "dashboard"),
            ("cobros", "💰 Cobros", "cobros"),
            ("pagos", "💸 Pagos", "pagos"),
            ("reportes", "📋 Reportes", "reportes"),
            ("categorias", "🏷️  Categorías", "categorias"),
            ("cuentas", "🏦 Cuentas", "cuentas"),
        ]
        
        for id_item, etiqueta, icono in items_nav:
            btn = QPushButton(etiqueta)
            btn.setObjectName("botonNav")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Marcar el índice como propiedad para poder identificarlo al hacer clic
            btn.setProperty("pantalla_id", id_item)
            
            # Conectar clic a cambio de pantalla
            btn.clicked.connect(lambda checked, pid=id_item: self._cambiar_pantalla(pid))
            
            layout.addWidget(btn)
            self.botones_nav[id_item] = btn
        
        # Espacio flexible para empujar los botones hacia arriba
        layout.addStretch()
        
        # Separador horizontal antes de opciones inferiores
        separador_inferior = QFrame()
        separador_inferior.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separador_inferior)
        
        # Botón de cerrar sesión / opciones
        btn_opciones = QPushButton("⚙️  Opciones")
        btn_opciones.setObjectName("botonNav")
        btn_opciones.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_opciones.clicked.connect(self._abrir_opciones)
        layout.addWidget(btn_opciones)
        
        btn_salir = QPushButton("🚪 Salir")
        btn_salir.setObjectName("botonNav")
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.clicked.connect(self.close)
        layout.addWidget(btn_salir)
        
        return sidebar
    
    def _crear_header(self) -> QFrame:
        """
        Crea el header superior con información del usuario.
        
        Retorna:
            QFrame con header
        """
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header.setStyleSheet("""
            #header {
                background-color: #ffffff;
                border-bottom: 1px solid #e8eaed;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)
        
        # Título de la pantalla actual
        self.label_titulo = QLabel("Dashboard")
        self.label_titulo.setObjectName("labelTitulo")
        font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        self.label_titulo.setFont(font)
        layout.addWidget(self.label_titulo)
        
        # Espacio flexible
        layout.addStretch()
        
        # Información del usuario (lado derecho)
        info_usuario = QLabel("👤 Usuario: Sistema")
        info_usuario.setObjectName("labelSubtitulo")
        layout.addWidget(info_usuario)
        
        return header
    
    def _cambiar_pantalla(self, id_pantalla: str):
        """
        Cambia a la pantalla indicada.
        
        Args:
            id_pantalla: Identificador de la pantalla (ej: "dashboard", "cobros")
        """
        # Si no existe, cargarla
        if id_pantalla not in self.pantallas:
            self._cargar_pantalla(id_pantalla)
        
        # Obtener la pantalla
        pantalla = self.pantallas.get(id_pantalla)
        if pantalla:
            # Cambiar en el stack widget
            self.stack_contenido.setCurrentWidget(pantalla)
            
            # Actualizar botón activo en sidebar
            self._actualizar_boton_activo(id_pantalla)
            
            # Actualizar título del header
            titulos = {
                "dashboard": "📈 Dashboard",
                "cobros": "💰 Cobros",
                "pagos": "💸 Pagos",
                "reportes": "📋 Reportes",
                "categorias": "🏷️  Categorías",
                "cuentas": "🏦 Cuentas",
            }
            self.label_titulo.setText(titulos.get(id_pantalla, id_pantalla))
    
    def _cargar_pantalla(self, id_pantalla: str):
        """
        Carga una pantalla bajo demanda.
        
        Args:
            id_pantalla: Identificador de la pantalla
        """
        # Crear la pantalla según el ID
        if id_pantalla == "dashboard":
            from app.ui.pantalla_dashboard import PantallaDashboard
            pantalla = PantallaDashboard()
        elif id_pantalla == "cobros":
            from app.ui.pantalla_cobros import PantallaCobros
            pantalla = PantallaCobros()
        elif id_pantalla == "pagos":
            from app.ui.pantalla_pagos import PantallaPagos
            pantalla = PantallaPagos()
        elif id_pantalla == "reportes":
            from app.ui.pantalla_reportes import PantallaReportes
            pantalla = PantallaReportes()
        elif id_pantalla == "categorias":
            # Placeholder por ahora
            pantalla = QWidget()
            layout = QVBoxLayout(pantalla)
            layout.addWidget(QLabel("Pantalla de Categorías (en desarrollo)"))
        elif id_pantalla == "cuentas":
            # Placeholder por ahora
            pantalla = QWidget()
            layout = QVBoxLayout(pantalla)
            layout.addWidget(QLabel("Pantalla de Cuentas (en desarrollo)"))
        else:
            pantalla = QWidget()
        
        # Guardar y agregar al stack
        self.pantallas[id_pantalla] = pantalla
        self.stack_contenido.addWidget(pantalla)
    
    def _actualizar_boton_activo(self, id_pantalla: str):
        """
        Marca el botón de navegación como activo.
        
        Args:
            id_pantalla: ID de la pantalla activa
        """
        for id_btn, btn in self.botones_nav.items():
            if id_btn == id_pantalla:
                btn.setProperty("class", "activo")
            else:
                btn.setProperty("class", "")
            
            # Redibujar el botón con los nuevos estilos
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def _cargar_estilos(self):
        """Carga el archivo QSS de estilos."""
        ruta_estilos = Path(__file__).parent / "estilos.qss"
        if not ruta_estilos.exists():
            # Si el archivo no está, buscar en la raíz del proyecto
            ruta_estilos = Path("app/ui/estilos.qss")
        
        if ruta_estilos.exists():
            with open(ruta_estilos, "r", encoding="utf-8") as archivo:
                estilos = archivo.read()
                self.setStyleSheet(estilos)
    
    def _conectar_senales(self):
        """Conecta señales de la aplicación."""
        # Por ahora vacío, se completa según necesidades
        pass
    
    def _abrir_opciones(self):
        """Abre un diálogo de opciones."""
        print("[INFO] Abriendo opciones...")
        # TODO: Implementar diálogo de opciones
    
    def _crear_icono(self) -> QIcon:
        """
        Crea un icono para la ventana (emoji o default).
        
        Retorna:
            QIcon
        """
        # Por ahora retornar un icono vacío (Qt lo maneja bien)
        return QIcon()


def main():
    """Función principal para pruebas."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    
    # Cargar el dashboard por defecto
    ventana._cambiar_pantalla("dashboard")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
