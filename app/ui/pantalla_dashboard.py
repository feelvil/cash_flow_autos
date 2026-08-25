"""
CASH FLOW AUTOS — Pantalla Dashboard
=====================================

Dashboard principal con vista de saldos en vivo, últimos movimientos y
resumen por categoría.

Componentes:
- Tarjeta de saldo general (grande, principal)
- Tarjetas de últimos cobros y pagos
- Resumen por automotriz (grid de tarjetas)
- Gráfico de evolución (opcional v1.1)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime

# Importar lógica de negocio
try:
    from app.logica.saldos import (
        obtener_saldo_general,
        obtener_saldo_por_automotriz,
        obtener_saldo_por_periodo,
    )
    from app.logica.reportes import movimientos_detallados
    BD_DISPONIBLE = True
except ImportError:
    BD_DISPONIBLE = False


class TarjetaSaldo(QFrame):
    """
    Tarjeta visual para mostrar un saldo o métrica.
    
    Estructura:
    ┌─────────────────────────┐
    │ Título (pequeño)        │
    │ $X.XXX.XXX,XX           │
    │ Subtítulo (gris)        │
    └─────────────────────────┘
    """
    
    def __init__(self, titulo: str, valor: str, subtitulo: str = "", tipo: str = "normal"):
        """
        Inicializa la tarjeta.
        
        Args:
            titulo: Título de la métrica (ej: "Saldo General")
            valor: Valor a mostrar (ej: "$4.613.352.569,94")
            subtitulo: Subtítulo descriptivo (ej: "Al día de hoy")
            tipo: Tipo de tarjeta ("normal", "cobro", "pago", "saldo")
        """
        super().__init__()
        
        self.tipo = tipo
        self.setObjectName(f"tarjeta{tipo.capitalize()}")
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Aplicar estilos según tipo
        if tipo == "cobro":
            self.setStyleSheet("""
                #tarjetacobro {
                    background-color: #ffffff;
                    border: 1px solid #e8eaed;
                    border-radius: 8px;
                    padding: 16px;
                    border-left: 4px solid #34a853;
                }
                #tarjetacobro:hover {
                    border: 1px solid #d0d7e0;
                }
            """)
        elif tipo == "pago":
            self.setStyleSheet("""
                #tarjetapago {
                    background-color: #ffffff;
                    border: 1px solid #e8eaed;
                    border-radius: 8px;
                    padding: 16px;
                    border-left: 4px solid #ea4335;
                }
                #tarjetapago:hover {
                    border: 1px solid #d0d7e0;
                }
            """)
        elif tipo == "saldo":
            self.setStyleSheet("""
                #tarjetasaldo {
                    background-color: #ffffff;
                    border: 1px solid #e8eaed;
                    border-radius: 8px;
                    padding: 20px;
                    border-left: 4px solid #1a73e8;
                }
                #tarjetasaldo:hover {
                    border: 1px solid #d0d7e0;
                }
            """)
        else:
            self.setStyleSheet("""
                #tarjeta {
                    background-color: #ffffff;
                    border: 1px solid #e8eaed;
                    border-radius: 8px;
                    padding: 16px;
                }
                #tarjeta:hover {
                    border: 1px solid #d0d7e0;
                }
            """)
        
        # Layout vertical para el contenido
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Título
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("tarjetaTitulo")
        font_titulo = QFont("Segoe UI", 12)
        font_titulo.setWeight(QFont.Weight.Medium)
        lbl_titulo.setFont(font_titulo)
        layout.addWidget(lbl_titulo)
        
        # Valor
        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("tarjetaValor")
        font_valor = QFont("Segoe UI", 24)
        font_valor.setWeight(QFont.Weight.Bold)
        lbl_valor.setFont(font_valor)
        layout.addWidget(lbl_valor)
        
        # Subtítulo
        if subtitulo:
            lbl_subtitulo = QLabel(subtitulo)
            lbl_subtitulo.setObjectName("tarjetaSubtitulo")
            font_subtitulo = QFont("Segoe UI", 10)
            lbl_subtitulo.setFont(font_subtitulo)
            layout.addWidget(lbl_subtitulo)
        
        layout.addStretch()


class PantallaDashboard(QWidget):
    """Pantalla principal del dashboard."""
    
    def __init__(self):
        """Inicializa el dashboard."""
        super().__init__()
        
        self._crear_ui()
        self._actualizar_datos()
        
        # Timer para actualizar datos cada 30 segundos
        self.timer = QTimer()
        self.timer.timeout.connect(self._actualizar_datos)
        self.timer.start(30000)  # 30 segundos
    
    def _crear_ui(self):
        """Crea la interfaz del dashboard."""
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(16)
        
        # ═════════════════════════════════════════════════════
        # FILA 1: Saldo General Grande
        # ═════════════════════════════════════════════════════
        self.tarjeta_saldo_general = TarjetaSaldo(
            titulo="Saldo General",
            valor="$0,00",
            subtitulo="Al día de hoy",
            tipo="saldo"
        )
        self.tarjeta_saldo_general.setMinimumHeight(140)
        layout_principal.addWidget(self.tarjeta_saldo_general)
        
        # ═════════════════════════════════════════════════════
        # FILA 2: Últimos movimientos (3 columnas)
        # ═════════════════════════════════════════════════════
        layout_ultimos = QHBoxLayout()
        layout_ultimos.setSpacing(16)
        
        self.tarjeta_ult_cobros = TarjetaSaldo(
            titulo="Últimos Cobros (7 días)",
            valor="$0,00",
            tipo="cobro"
        )
        layout_ultimos.addWidget(self.tarjeta_ult_cobros)
        
        self.tarjeta_ult_pagos = TarjetaSaldo(
            titulo="Últimos Pagos (7 días)",
            valor="$0,00",
            tipo="pago"
        )
        layout_ultimos.addWidget(self.tarjeta_ult_pagos)
        
        self.tarjeta_neto = TarjetaSaldo(
            titulo="Neto (7 días)",
            valor="$0,00",
            tipo="normal"
        )
        layout_ultimos.addWidget(self.tarjeta_neto)
        
        layout_principal.addLayout(layout_ultimos)
        
        # ═════════════════════════════════════════════════════
        # FILA 3: Resumen por Automotriz (grid dinámico)
        # ═════════════════════════════════════════════════════
        lbl_titulo_auto = QLabel("Saldo por Grupo Automotriz")
        font_titulo = QFont("Segoe UI", 14)
        font_titulo.setWeight(QFont.Weight.Bold)
        lbl_titulo_auto.setFont(font_titulo)
        layout_principal.addWidget(lbl_titulo_auto)
        
        # Grid scroll para las tarjetas de automotrices
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        
        widget_scroll = QWidget()
        self.layout_autos = QGridLayout(widget_scroll)
        self.layout_autos.setSpacing(12)
        
        scroll.setWidget(widget_scroll)
        layout_principal.addWidget(scroll, 1)  # Tomar espacio flexible
        
        # ═════════════════════════════════════════════════════
        # FILA 4: Botones de acción rápida
        # ═════════════════════════════════════════════════════
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(8)
        
        btn_nuevo_cobro = QPushButton("➕ Nuevo Cobro")
        btn_nuevo_cobro.clicked.connect(self._ir_a_cobros)
        layout_botones.addWidget(btn_nuevo_cobro)
        
        btn_nuevo_pago = QPushButton("➕ Nuevo Pago")
        btn_nuevo_pago.clicked.connect(self._ir_a_pagos)
        layout_botones.addWidget(btn_nuevo_pago)
        
        btn_ver_reportes = QPushButton("📊 Ver Reportes")
        btn_ver_reportes.setObjectName("botonSecundario")
        btn_ver_reportes.clicked.connect(self._ir_a_reportes)
        layout_botones.addWidget(btn_ver_reportes)
        
        layout_botones.addStretch()
        
        layout_principal.addLayout(layout_botones)
    
    def _actualizar_datos(self):
        """Actualiza los datos del dashboard desde la base de datos."""
        
        if not BD_DISPONIBLE:
            # Mostrar datos de prueba si la BD no está disponible
            self._mostrar_datos_prueba()
            return
        
        try:
            # ═════════════════════════════════════════════════════
            # SALDO GENERAL
            # ═════════════════════════════════════════════════════
            saldo_general = obtener_saldo_general()
            valor_formateado = self._formatear_moneda(saldo_general)
            self.tarjeta_saldo_general.findChild(QLabel, "tarjetaValor").setText(valor_formateado)
            
            # ═════════════════════════════════════════════════════
            # ÚLTIMOS 7 DÍAS
            # ═════════════════════════════════════════════════════
            # TODO: Implementar función de últimos movimientos por período
            # Por ahora usar datos de prueba
            
            # ═════════════════════════════════════════════════════
            # SALDO POR AUTOMOTRIZ (GRUPOS)
            # ═════════════════════════════════════════════════════
            saldos_auto = obtener_saldo_por_automotriz()
            self._llenar_grid_automotrices(saldos_auto)
            
        except Exception as e:
            print(f"[ERROR] No se pudieron actualizar los datos del dashboard: {e}")
            self._mostrar_datos_prueba()
    
    def _llenar_grid_automotrices(self, saldos_auto: dict):
        """
        Llena el grid de tarjetas de automotrices.
        
        Args:
            saldos_auto: Dict con {nombre_auto: saldo}
        """
        # Limpiar grid anterior
        while self.layout_autos.count():
            item = self.layout_autos.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Agregar tarjetas (3 por fila)
        fila = 0
        col = 0
        for nombre_auto, saldo in sorted(saldos_auto.items()):
            tarjeta = TarjetaSaldo(
                titulo=nombre_auto,
                valor=self._formatear_moneda(saldo),
                tipo="normal"
            )
            self.layout_autos.addWidget(tarjeta, fila, col)
            
            col += 1
            if col >= 3:
                col = 0
                fila += 1
    
    def _mostrar_datos_prueba(self):
        """Muestra datos de prueba para desarrollo (sin BD)."""
        self.tarjeta_saldo_general.findChild(
            QLabel, "tarjetaValor"
        ).setText("$4.613.352.569,94")
        
        # Últimos 7 días (prueba)
        self.tarjeta_ult_cobros.findChild(
            QLabel, "tarjetaValor"
        ).setText("$1.250.000,00")
        
        self.tarjeta_ult_pagos.findChild(
            QLabel, "tarjetaValor"
        ).setText("$850.000,00")
        
        self.tarjeta_neto.findChild(
            QLabel, "tarjetaValor"
        ).setText("$400.000,00")
        
        # Automotrices (datos de prueba)
        saldos_prueba = {
            "1 - VW - Volkswagen": 1500000000.00,
            "2 - PR - Plan Rombo": 2000000000.00,
            "3 - GM - Chevrolet": 800000000.00,
            "4 - FCA - Fiat": 250000000.00,
            "5 - YAM - Yamaha": 63352569.94,
        }
        self._llenar_grid_automotrices(saldos_prueba)
    
    @staticmethod
    def _formatear_moneda(valor: float) -> str:
        """
        Formatea un número como moneda en pesos argentinos.
        
        Args:
            valor: Valor numérico
        
        Retorna:
            String formateado (ej: "$1.234.567,89")
        """
        # Formatear con miles y 2 decimales
        # En Argentina: punto para miles, coma para decimales
        valor_formateado = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
        return f"${valor_formateado}"
    
    def _ir_a_cobros(self):
        """Navega a la pantalla de cobros."""
        # TODO: Emitir señal o llamar método de ventana principal
        print("[INFO] Navegar a Cobros")
    
    def _ir_a_pagos(self):
        """Navega a la pantalla de pagos."""
        print("[INFO] Navegar a Pagos")
    
    def _ir_a_reportes(self):
        """Navega a la pantalla de reportes."""
        print("[INFO] Navegar a Reportes")
    
    def closeEvent(self, event):
        """Detiene el timer al cerrar la pantalla."""
        self.timer.stop()
        super().closeEvent(event)


def main():
    """Función principal para pruebas."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    ventana = PantallaDashboard()
    ventana.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
