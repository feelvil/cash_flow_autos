"""
CASH FLOW AUTOS — Pantalla de Reportes
=======================================

Pantalla de consulta de datos con:
- Filtros (período, clasificación, automotriz)
- Tabla de movimientos con totales
- Exportación a Excel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QFrame, QFileDialog, QSpinBox
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from pathlib import Path

# Importar lógica de negocio
try:
    from app.logica.reportes import (
        movimientos_detallados,
        resumen_por_clasificacion,
        totales_filtrados,
    )
    from app.utils.exportar_excel import exportar_movimientos, exportar_resumen
    BD_DISPONIBLE = True
except ImportError:
    BD_DISPONIBLE = False


class PantallaReportes(QWidget):
    """Pantalla de reportes y consultas."""
    
    def __init__(self):
        """Inicializa la pantalla de reportes."""
        super().__init__()
        
        self._crear_ui()
        self._actualizar_tabla()
    
    def _crear_ui(self):
        """Crea la interfaz de la pantalla."""
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(16)
        
        # ═════════════════════════════════════════════════════
        # SECCIÓN 1: FILTROS
        # ═════════════════════════════════════════════════════
        
        lbl_titulo_filtros = QLabel("Filtros de Búsqueda")
        font_titulo = QFont("Segoe UI", 14)
        font_titulo.setWeight(QFont.Weight.Bold)
        lbl_titulo_filtros.setFont(font_titulo)
        layout_principal.addWidget(lbl_titulo_filtros)
        
        # Frame para los filtros
        frame_filtros = QFrame()
        frame_filtros.setStyleSheet("""
            #frameForm {
                background-color: #ffffff;
                border: 1px solid #e8eaed;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        frame_filtros.setObjectName("frameForm")
        layout_filtros = QHBoxLayout(frame_filtros)
        layout_filtros.setSpacing(12)
        
        # Rango de fechas
        layout_filtros.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_desde.setCalendarPopup(True)
        layout_filtros.addWidget(self.fecha_desde)
        
        layout_filtros.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setCalendarPopup(True)
        layout_filtros.addWidget(self.fecha_hasta)
        
        # Tipo de movimiento
        layout_filtros.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Todos", "Cobros", "Pagos"])
        layout_filtros.addWidget(self.combo_tipo)
        
        # Clasificación
        layout_filtros.addWidget(QLabel("Clasificación:"))
        self.combo_clasificacion = QComboBox()
        self.combo_clasificacion.addItems([
            "Todas",
            "Por Partida",
            "Por Sub-Partida",
            "Por Automotriz"
        ])
        layout_filtros.addWidget(self.combo_clasificacion)
        
        # Botones de acción
        btn_filtrar = QPushButton("🔍 Filtrar")
        btn_filtrar.clicked.connect(self._aplicar_filtros)
        layout_filtros.addWidget(btn_filtrar)
        
        btn_limpiar_filtros = QPushButton("❌ Limpiar")
        btn_limpiar_filtros.setObjectName("botonSecundario")
        btn_limpiar_filtros.clicked.connect(self._limpiar_filtros)
        layout_filtros.addWidget(btn_limpiar_filtros)
        
        layout_filtros.addStretch()
        
        layout_principal.addWidget(frame_filtros)
        
        # ═════════════════════════════════════════════════════
        # SECCIÓN 2: TABLA DE RESULTADOS
        # ═════════════════════════════════════════════════════
        
        lbl_titulo_tabla = QLabel("Movimientos")
        lbl_titulo_tabla.setFont(font_titulo)
        layout_principal.addWidget(lbl_titulo_tabla)
        
        # Tabla
        self.tabla_reportes = QTableWidget()
        self.tabla_reportes.setColumnCount(8)
        self.tabla_reportes.setHorizontalHeaderLabels([
            "Fecha", "Código", "Partida", "Tipo Op.", 
            "Cobro", "Pago", "Neto", "Saldo Acumulado"
        ])
        self.tabla_reportes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_reportes.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_reportes.setAlternatingRowColors(True)
        
        # Estilos
        self.tabla_reportes.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e8eaed;
                border: 1px solid #e8eaed;
                border-radius: 4px;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #e8eaed;
                font-weight: 600;
                font-size: 11px;
            }
        """)
        
        layout_principal.addWidget(self.tabla_reportes, 1)
        
        # ═════════════════════════════════════════════════════
        # SECCIÓN 3: BOTONES DE EXPORTACIÓN
        # ═════════════════════════════════════════════════════
        
        layout_botones_export = QHBoxLayout()
        layout_botones_export.setSpacing(8)
        
        btn_exportar_movimientos = QPushButton("📊 Exportar Movimientos a Excel")
        btn_exportar_movimientos.clicked.connect(self._exportar_movimientos)
        layout_botones_export.addWidget(btn_exportar_movimientos)
        
        btn_exportar_resumen = QPushButton("📈 Exportar Resumen a Excel")
        btn_exportar_resumen.setObjectName("botonSecundario")
        btn_exportar_resumen.clicked.connect(self._exportar_resumen)
        layout_botones_export.addWidget(btn_exportar_resumen)
        
        layout_botones_export.addStretch()
        
        layout_principal.addLayout(layout_botones_export)
    
    def _aplicar_filtros(self):
        """Aplica los filtros y actualiza la tabla."""
        self._actualizar_tabla()
    
    def _limpiar_filtros(self):
        """Limpia todos los filtros."""
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_hasta.setDate(QDate.currentDate())
        self.combo_tipo.setCurrentIndex(0)
        self.combo_clasificacion.setCurrentIndex(0)
        self._actualizar_tabla()
    
    def _actualizar_tabla(self):
        """Actualiza la tabla según los filtros seleccionados."""
        
        self.tabla_reportes.setRowCount(0)
        
        if not BD_DISPONIBLE:
            self._mostrar_datos_prueba()
            return
        
        try:
            # Obtener filtros
            tipo = self.combo_tipo.currentText()
            filtro_tipo = {
                "Cobros": "cobro",
                "Pagos": "pago",
                "Todos": None
            }.get(tipo)
            
            fecha_desde = self.fecha_desde.date().toPython()
            fecha_hasta = self.fecha_hasta.date().toPython()
            
            # Obtener movimientos
            movimientos = movimientos_detallados(
                filtro_tipo=filtro_tipo,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                limite=500
            )
            
            # Llenar tabla
            for idx, mov in enumerate(movimientos):
                self.tabla_reportes.insertRow(idx)
                
                # Fecha
                self.tabla_reportes.setItem(
                    idx, 0, QTableWidgetItem(str(mov.get("fecha", "")))
                )
                
                # Código
                self.tabla_reportes.setItem(
                    idx, 1, QTableWidgetItem(str(mov.get("codigo", "")))
                )
                
                # Partida
                self.tabla_reportes.setItem(
                    idx, 2, QTableWidgetItem(mov.get("partida", ""))
                )
                
                # Tipo Operación
                self.tabla_reportes.setItem(
                    idx, 3, QTableWidgetItem(mov.get("tipo_operacion", ""))
                )
                
                # Cobro (verde)
                cobro = float(mov.get("ingresos", 0))
                if cobro > 0:
                    item_cobro = QTableWidgetItem(f"${cobro:,.2f}")
                    item_cobro.setForeground(QColor("#34a853"))
                    self.tabla_reportes.setItem(idx, 4, item_cobro)
                else:
                    self.tabla_reportes.setItem(idx, 4, QTableWidgetItem(""))
                
                # Pago (rojo)
                pago = float(mov.get("egresos", 0))
                if pago > 0:
                    item_pago = QTableWidgetItem(f"${pago:,.2f}")
                    item_pago.setForeground(QColor("#ea4335"))
                    self.tabla_reportes.setItem(idx, 5, item_pago)
                else:
                    self.tabla_reportes.setItem(idx, 5, QTableWidgetItem(""))
                
                # Neto
                neto = float(mov.get("neto", 0))
                item_neto = QTableWidgetItem(f"${neto:,.2f}")
                if neto > 0:
                    item_neto.setForeground(QColor("#34a853"))
                else:
                    item_neto.setForeground(QColor("#ea4335"))
                self.tabla_reportes.setItem(idx, 6, item_neto)
                
                # Saldo acumulado
                saldo_acum = float(mov.get("saldo_acumulado", 0))
                item_saldo = QTableWidgetItem(f"${saldo_acum:,.2f}")
                item_saldo.setForeground(QColor("#1a73e8"))
                self.tabla_reportes.setItem(idx, 7, item_saldo)
            
            # Ajustar ancho de columnas
            self.tabla_reportes.resizeColumnsToContents()
            
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar los reportes: {e}")
            self._mostrar_datos_prueba()
    
    def _mostrar_datos_prueba(self):
        """Muestra datos de prueba."""
        
        datos_prueba = [
            ("2026-01-15", "1041131", "INGRESOS", "Transferencia", 17531900.00, 0, 17531900.00, 4613352569.94),
            ("2026-01-14", "2010001", "EGRESOS", "BtoB", 0, 2500000.00, -2500000.00, 4595820669.94),
            ("2026-01-13", "1045451", "INGRESOS", "Transferencia", 2500000.00, 0, 2500000.00, 4598320669.94),
            ("2026-01-12", "2020001", "EGRESOS", "Transferencia", 0, 50000000.00, -50000000.00, 4595820669.94),
            ("2026-01-11", "1041132", "INGRESOS", "Transferencia", 5000000.00, 0, 5000000.00, 4645820669.94),
        ]
        
        for idx, (fecha, cod, part, tipo_op, cobro, pago, neto, saldo) in enumerate(datos_prueba):
            self.tabla_reportes.insertRow(idx)
            
            self.tabla_reportes.setItem(idx, 0, QTableWidgetItem(fecha))
            self.tabla_reportes.setItem(idx, 1, QTableWidgetItem(cod))
            self.tabla_reportes.setItem(idx, 2, QTableWidgetItem(part))
            self.tabla_reportes.setItem(idx, 3, QTableWidgetItem(tipo_op))
            
            if cobro > 0:
                item_cobro = QTableWidgetItem(f"${cobro:,.2f}")
                item_cobro.setForeground(QColor("#34a853"))
                self.tabla_reportes.setItem(idx, 4, item_cobro)
            
            if pago > 0:
                item_pago = QTableWidgetItem(f"${pago:,.2f}")
                item_pago.setForeground(QColor("#ea4335"))
                self.tabla_reportes.setItem(idx, 5, item_pago)
            
            item_neto = QTableWidgetItem(f"${neto:,.2f}")
            item_neto.setForeground(QColor("#34a853" if neto > 0 else "#ea4335"))
            self.tabla_reportes.setItem(idx, 6, item_neto)
            
            item_saldo = QTableWidgetItem(f"${saldo:,.2f}")
            item_saldo.setForeground(QColor("#1a73e8"))
            self.tabla_reportes.setItem(idx, 7, item_saldo)
    
    def _exportar_movimientos(self):
        """Exporta los movimientos a un archivo Excel."""
        
        if not BD_DISPONIBLE:
            QMessageBox.warning(self, "Error", "Base de datos no disponible")
            return
        
        try:
            # Pedir ubicación para guardar el archivo
            ruta_archivo, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar movimientos como Excel",
                str(Path.home() / f"Movimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"),
                "Archivos Excel (*.xlsx)"
            )
            
            if not ruta_archivo:
                return
            
            # Exportar
            ruta = exportar_movimientos(Path(ruta_archivo))
            
            QMessageBox.information(
                self,
                "Éxito",
                f"Archivo guardado exitosamente:\n{ruta}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")
    
    def _exportar_resumen(self):
        """Exporta un resumen de movimientos a Excel."""
        
        if not BD_DISPONIBLE:
            QMessageBox.warning(self, "Error", "Base de datos no disponible")
            return
        
        try:
            # Pedir ubicación para guardar
            ruta_archivo, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar resumen como Excel",
                str(Path.home() / f"Resumen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"),
                "Archivos Excel (*.xlsx)"
            )
            
            if not ruta_archivo:
                return
            
            # Exportar resumen por partida
            dimension = "partida"  # Puede cambiar según filtro
            ruta = exportar_resumen(
                dimension=dimension,
                ruta=Path(ruta_archivo)
            )
            
            QMessageBox.information(
                self,
                "Éxito",
                f"Resumen guardado exitosamente:\n{ruta}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {str(e)}")


def main():
    """Función principal para pruebas."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    ventana = PantallaReportes()
    ventana.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
