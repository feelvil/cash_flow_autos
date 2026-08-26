"""
Pantalla de Reportes: filtros y exportación.

Permite:
- Filtrar movimientos por período, categoría, etc.
- Visualizar en tabla
- Exportar a Excel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDateEdit, QHeaderView, QMessageBox
)
from PySide6.QtCore import QDate

from app.logica.saldos import movimientos_detallados
from app.logica.reportes import generar_reporte_excel


class PantallarePortes(QWidget):
    """
    Pantalla de reportes.
    
    Permite:
    - Filtrar movimientos por fecha
    - Visualizar en tabla
    - Exportar a Excel
    """
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Título
        titulo = QLabel("Reportes")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(titulo)
        
        # Filtros
        layout_filtros = self._crear_filtros()
        layout.addLayout(layout_filtros)
        
        # Tabla de resultados
        layout.addWidget(QLabel("Movimientos"))
        self.tabla_resultados = self._crear_tabla_resultados()
        layout.addWidget(self.tabla_resultados)
        
        # Botones de exportación
        layout_exportar = QHBoxLayout()
        
        btn_exportar = QPushButton("Exportar a Excel")
        btn_exportar.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            """
        )
        btn_exportar.clicked.connect(self._exportar_a_excel)
        
        layout_exportar.addStretch()
        layout_exportar.addWidget(btn_exportar)
        layout.addLayout(layout_exportar)
        
        # Cargar datos iniciales
        self._cargar_reportes()
    
    def _crear_filtros(self) -> QHBoxLayout:
        """Crear controles de filtro."""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        # Fecha inicio
        layout.addWidget(QLabel("Desde"))
        self.input_fecha_inicio = QDateEdit()
        self.input_fecha_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.input_fecha_inicio.setCalendarPopup(True)
        self.input_fecha_inicio.dateChanged.connect(self._cargar_reportes)
        layout.addWidget(self.input_fecha_inicio)
        
        # Fecha fin
        layout.addWidget(QLabel("Hasta"))
        self.input_fecha_fin = QDateEdit()
        self.input_fecha_fin.setDate(QDate.currentDate())
        self.input_fecha_fin.setCalendarPopup(True)
        self.input_fecha_fin.dateChanged.connect(self._cargar_reportes)
        layout.addWidget(self.input_fecha_fin)
        
        # Botón actualizar
        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.clicked.connect(self._cargar_reportes)
        layout.addWidget(btn_actualizar)
        
        layout.addStretch()
        
        return layout
    
    def _crear_tabla_resultados(self) -> QTableWidget:
        """Crear tabla de resultados."""
        tabla = QTableWidget()
        tabla.setColumnCount(6)
        tabla.setHorizontalHeaderLabels([
            "Fecha", "Código", "Sub-partida", "Comprobante", "Monto", "Saldo"
        ])
        
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        
        return tabla
    
    def _cargar_reportes(self):
        """Cargar datos de reportes según filtros."""
        try:
            fecha_inicio = self.input_fecha_inicio.date().toPython()
            fecha_fin = self.input_fecha_fin.date().toPython()
            
            # Obtener movimientos en rango
            movimientos = movimientos_detallados(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                solo_activos=True
            )
            
            # Llenar tabla
            self.tabla_resultados.setRowCount(len(movimientos))
            
            saldo_acum = 0
            for fila, mov in enumerate(movimientos):
                saldo_acum += (mov.get('ingresos', 0) - mov.get('egresos', 0))
                
                # Fecha
                fecha_str = mov.get('fecha', '').strftime('%d/%m/%Y') if mov.get('fecha') else ""
                self.tabla_resultados.setItem(fila, 0, QTableWidgetItem(fecha_str))
                
                # Código
                codigo_str = str(mov.get('codigo', ''))
                self.tabla_resultados.setItem(fila, 1, QTableWidgetItem(codigo_str))
                
                # Sub-partida
                sub_partida = mov.get('sub_partida', '')
                self.tabla_resultados.setItem(fila, 2, QTableWidgetItem(sub_partida))
                
                # Comprobante
                comprobante = mov.get('comprobante', '') or ""
                self.tabla_resultados.setItem(fila, 3, QTableWidgetItem(comprobante))
                
                # Monto
                ingreso = mov.get('ingresos', 0)
                egreso = mov.get('egresos', 0)
                monto = ingreso - egreso
                monto_str = f"${monto:,.2f}"
                self.tabla_resultados.setItem(fila, 4, QTableWidgetItem(monto_str))
                
                # Saldo acumulado
                saldo_str = f"${saldo_acum:,.2f}"
                self.tabla_resultados.setItem(fila, 5, QTableWidgetItem(saldo_str))
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar reportes: {str(e)}")
    
    def _exportar_a_excel(self):
        """Exportar tabla a archivo Excel."""
        try:
            fecha_inicio = self.input_fecha_inicio.date().toPython()
            fecha_fin = self.input_fecha_fin.date().toPython()
            
            # TODO: Implementar exportación a Excel en app/utils/exportar_excel.py
            # Por ahora, solo mostrar mensaje
            QMessageBox.information(
                self,
                "Exportación",
                "La exportación a Excel será implementada en v1.1"
            )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
