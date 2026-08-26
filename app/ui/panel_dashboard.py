"""
Panel Dashboard: pantalla principal con resumen de saldos.

Muestra:
- Saldo total actual
- Últimos movimientos
- Gráfico básico de saldos por período (opcional)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate

# Importar funciones de lógica
from app.logica.saldos import calcular_saldo_total, movimientos_detallados


class PanelDashboard(QWidget):
    """
    Panel principal (Dashboard) de la aplicación.
    
    Estructura:
    - Header con saldo total
    - Tabla de últimos 20 movimientos
    """
    
    def __init__(self):
        super().__init__()
        
        # Crear layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # ========================================================================
        # TÍTULO
        # ========================================================================
        titulo = QLabel("Dashboard")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(titulo)
        
        # ========================================================================
        # SALDO TOTAL
        # ========================================================================
        layout_saldo = self._crear_seccion_saldos()
        layout.addLayout(layout_saldo)
        
        # ========================================================================
        # ÚLTIMOS MOVIMIENTOS
        # ========================================================================
        layout.addWidget(QLabel("Últimos movimientos"))
        
        self.tabla_movimientos = self._crear_tabla_movimientos()
        layout.addWidget(self.tabla_movimientos)
        
        # Cargar datos
        self._actualizar_datos()
    
    def _crear_seccion_saldos(self) -> QHBoxLayout:
        """
        Crear la sección de saldos.
        
        Muestra:
        - Saldo total actual
        - Indicador de aumento/disminución
        """
        layout = QHBoxLayout()
        layout.setSpacing(24)
        
        # Card de saldo total
        saldo_total = calcular_saldo_total()
        
        # Label saldo
        label_saldo_titulo = QLabel("Saldo total")
        label_saldo_titulo.setStyleSheet("color: #999; font-size: 12px;")
        
        label_saldo_valor = QLabel(f"${saldo_total:,.2f}")
        label_saldo_valor.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #2196F3;"
        )
        
        layout_saldo = QVBoxLayout()
        layout_saldo.addWidget(label_saldo_titulo)
        layout_saldo.addWidget(label_saldo_valor)
        layout_saldo.addStretch()
        
        layout.addLayout(layout_saldo)
        layout.addStretch()
        
        return layout
    
    def _crear_tabla_movimientos(self) -> QTableWidget:
        """
        Crear tabla con últimos movimientos.
        
        Columnas:
        - Fecha
        - Código (plan de cuentas)
        - Sub-partida
        - Comprobante
        - Ingreso / Egreso
        - Saldo acumulado
        """
        tabla = QTableWidget()
        tabla.setColumnCount(6)
        tabla.setHorizontalHeaderLabels([
            "Fecha", "Código", "Sub-partida", "Comprobante", "Monto", "Saldo"
        ])
        
        # Configurar ancho de columnas
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Sub-partida
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Comprobante
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Monto
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Saldo
        
        # Altura de filas
        tabla.setRowHeight(0, 40)
        tabla.setMaximumHeight(400)
        
        # No editable
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        
        return tabla
    
    def _actualizar_datos(self):
        """
        Cargar datos desde la BD y actualizar las tablas.
        
        Obtiene:
        - Últimos 20 movimientos sin anular
        - Calcula saldo acumulado
        """
        try:
            # Obtener movimientos (últimos 20, sin anular)
            movimientos = movimientos_detallados(
                limite=20,
                solo_activos=True,
                ordenar_descendente=True
            )
            
            # Llenar tabla
            self.tabla_movimientos.setRowCount(len(movimientos))
            
            saldo_acum = 0
            for fila, mov in enumerate(movimientos):
                # Actualizar saldo acumulado
                saldo_acum += (mov.get('ingresos', 0) - mov.get('egresos', 0))
                
                # Fecha
                fecha_str = mov.get('fecha', '').strftime('%d/%m/%Y') if mov.get('fecha') else ""
                self.tabla_movimientos.setItem(fila, 0, QTableWidgetItem(fecha_str))
                
                # Código
                codigo_str = str(mov.get('codigo', ''))
                self.tabla_movimientos.setItem(fila, 1, QTableWidgetItem(codigo_str))
                
                # Sub-partida
                sub_partida = mov.get('sub_partida', '')
                self.tabla_movimientos.setItem(fila, 2, QTableWidgetItem(sub_partida))
                
                # Comprobante
                comprobante = mov.get('comprobante', '') or ""
                self.tabla_movimientos.setItem(fila, 3, QTableWidgetItem(comprobante))
                
                # Monto (ingreso o egreso)
                ingreso = mov.get('ingresos', 0)
                egreso = mov.get('egresos', 0)
                monto = ingreso - egreso
                monto_str = f"${monto:,.2f}"
                
                # Color: verde si ingreso, rojo si egreso
                item_monto = QTableWidgetItem(monto_str)
                if monto > 0:
                    item_monto.setForeground(Qt.green)
                elif monto < 0:
                    item_monto.setForeground(Qt.red)
                
                self.tabla_movimientos.setItem(fila, 4, item_monto)
                
                # Saldo acumulado
                saldo_str = f"${saldo_acum:,.2f}"
                self.tabla_movimientos.setItem(fila, 5, QTableWidgetItem(saldo_str))
        
        except Exception as e:
            # Si hay error, mostrar un label con el error
            print(f"Error al cargar datos del dashboard: {e}")
