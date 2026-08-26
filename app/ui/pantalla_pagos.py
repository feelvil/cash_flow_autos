"""
CASH FLOW AUTOS — Pantalla de Pagos
====================================

Pantalla para registrar pagos (egresos).

Estructura:
- Formulario de carga (código, comprobante, monto, descripción)
- Tabla de últimos pagos registrados
- Validaciones y manejo de errores
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QMessageBox, QFrame, QSpinBox
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta

# Importar lógica de negocio
try:
    from app.logica.movimientos import crear_movimiento
    from app.logica.reportes import movimientos_detallados
    from app.logica.catalogos import obtener_codigos_pago
    BD_DISPONIBLE = True
except ImportError:
    BD_DISPONIBLE = False


# Códigos de respaldo si la BD no está disponible (modo prueba / sin conexión).
CODIGOS_PRUEBA_PAGO = [
    "2010001 — Registración · Registración de unidades",
    "2010002 — Registración · Comisiones",
    "2020001 — Sueldos · Sueldos",
    "2020002 — Sueldos · Cargas sociales",
    "2030001 — Servicios · Luz, gas, teléfono",
    "2030002 — Alquileres",
    "2040001 — Impuestos",
    "2050001 — Otros gastos",
]


class PantallaPagos(QWidget):
    """Pantalla para registrar pagos (egresos)."""
    
    def __init__(self):
        """Inicializa la pantalla de pagos."""
        super().__init__()
        
        self._crear_ui()
        self._actualizar_tabla()
        
        # Timer para actualizar tabla cada 15 segundos
        self.timer = QTimer()
        self.timer.timeout.connect(self._actualizar_tabla)
        self.timer.start(15000)
    
    def _crear_ui(self):
        """Crea la interfaz de la pantalla."""
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(16)
        
        # ═════════════════════════════════════════════════════
        # SECCIÓN 1: FORMULARIO DE CARGA
        # ═════════════════════════════════════════════════════
        
        # Título de la sección
        lbl_titulo_form = QLabel("Registrar Nuevo Pago")
        font_titulo = QFont("Segoe UI", 14)
        font_titulo.setWeight(QFont.Weight.Bold)
        lbl_titulo_form.setFont(font_titulo)
        layout_principal.addWidget(lbl_titulo_form)
        
        # Frame para el formulario
        frame_form = QFrame()
        frame_form.setStyleSheet("""
            #frameForm {
                background-color: #ffffff;
                border: 1px solid #e8eaed;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        frame_form.setObjectName("frameForm")
        layout_form = QVBoxLayout(frame_form)
        layout_form.setSpacing(12)
        
        # ═════════════════════════════════════════════════════
        # FILA 1: Código y Fecha
        # ═════════════════════════════════════════════════════
        layout_f1 = QHBoxLayout()
        layout_f1.setSpacing(12)
        
        # Código (combo auto-completable, se llena desde la BD)
        layout_f1.addWidget(QLabel("Código de Cuenta:"))
        self.combo_codigo = QComboBox()
        self.combo_codigo.setEditable(True)
        self.combo_codigo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._cargar_codigos()  # llena el combo con datos reales (o de prueba)
        layout_f1.addWidget(self.combo_codigo, 1)
        
        # Fecha
        layout_f1.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout_f1.addWidget(self.input_fecha)
        
        layout_form.addLayout(layout_f1)
        
        # ═════════════════════════════════════════════════════
        # FILA 2: Comprobante y Monto
        # ═════════════════════════════════════════════════════
        layout_f2 = QHBoxLayout()
        layout_f2.setSpacing(12)
        
        # Comprobante
        layout_f2.addWidget(QLabel("Comprobante:"))
        self.input_comprobante = QLineEdit()
        self.input_comprobante.setPlaceholderText("Ej: FC 0009-00002632 o Cheque Nº 123456")
        layout_f2.addWidget(self.input_comprobante, 1)
        
        # Monto
        layout_f2.addWidget(QLabel("Monto ($):"))
        self.input_monto = QDoubleSpinBox()
        self.input_monto.setMinimum(0.0)
        self.input_monto.setMaximum(999999999999.99)
        self.input_monto.setDecimals(2)
        self.input_monto.setSingleStep(1000.0)
        layout_f2.addWidget(self.input_monto)
        
        layout_form.addLayout(layout_f2)
        
        # ═════════════════════════════════════════════════════
        # FILA 3: Descripción
        # ═════════════════════════════════════════════════════
        layout_f3 = QHBoxLayout()
        layout_f3.setSpacing(12)
        
        layout_f3.addWidget(QLabel("Descripción (opcional):"))
        self.input_descripcion = QLineEdit()
        self.input_descripcion.setPlaceholderText("Observaciones o detalles adicionales")
        layout_f3.addWidget(self.input_descripcion)
        
        layout_form.addLayout(layout_f3)
        
        # ═════════════════════════════════════════════════════
        # FILA 4: Botones de acción
        # ═════════════════════════════════════════════════════
        layout_f4 = QHBoxLayout()
        layout_f4.setSpacing(8)
        
        btn_guardar = QPushButton("💾 Guardar Pago")
        btn_guardar.setObjectName("botonPeligro")
        btn_guardar.clicked.connect(self._guardar_pago)
        layout_f4.addWidget(btn_guardar)
        
        btn_limpiar = QPushButton("🗑️  Limpiar")
        btn_limpiar.setObjectName("botonSecundario")
        btn_limpiar.clicked.connect(self._limpiar_formulario)
        layout_f4.addWidget(btn_limpiar)
        
        layout_f4.addStretch()
        
        layout_form.addLayout(layout_f4)
        
        layout_principal.addWidget(frame_form)
        
        # ═════════════════════════════════════════════════════
        # SECCIÓN 2: TABLA DE ÚLTIMOS PAGOS
        # ═════════════════════════════════════════════════════
        
        lbl_titulo_tabla = QLabel("Últimos Pagos Registrados")
        font_titulo = QFont("Segoe UI", 14)
        font_titulo.setWeight(QFont.Weight.Bold)
        lbl_titulo_tabla.setFont(font_titulo)
        layout_principal.addWidget(lbl_titulo_tabla)
        
        # Tabla
        self.tabla_pagos = QTableWidget()
        self.tabla_pagos.setColumnCount(6)
        self.tabla_pagos.setHorizontalHeaderLabels([
            "Fecha", "Código", "Comprobante", "Monto", "Usuario", "Estado"
        ])
        self.tabla_pagos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_pagos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_pagos.setAlternatingRowColors(True)
        self.tabla_pagos.setMinimumHeight(200)
        
        # Estilos de tabla
        self.tabla_pagos.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e8eaed;
                border: 1px solid #e8eaed;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #fadbd8;
                color: #ea4335;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                color: #2c3e50;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #e8eaed;
                font-weight: 600;
                font-size: 12px;
            }
        """)
        
        layout_principal.addWidget(self.tabla_pagos, 1)  # Tomar espacio flexible
    
    def _cargar_codigos(self):
        """
        Llena el combo de códigos con datos reales de la BD (partidas EGRESOS).
        
        Cada item guarda el texto visible y, oculto, el código numérico
        (userData) que usamos al guardar. Si la BD no está disponible, cae a
        una lista de prueba para que la pantalla siga usable en desarrollo.
        """
        self.combo_codigo.clear()
        
        if not BD_DISPONIBLE:
            self.combo_codigo.addItems(CODIGOS_PRUEBA_PAGO)
            return
        
        try:
            codigos = obtener_codigos_pago()
            if not codigos:
                self.combo_codigo.addItems(CODIGOS_PRUEBA_PAGO)
                return
            
            for c in codigos:
                self.combo_codigo.addItem(c.etiqueta(), userData=c.codigo)
                
        except Exception as e:
            print(f"[DEBUG] No se pudieron cargar códigos de la BD: {e}")
            self.combo_codigo.addItems(CODIGOS_PRUEBA_PAGO)
    
    def _resolver_codigo(self) -> int:
        """
        Devuelve el código numérico elegido en el combo, de forma robusta.
        
        Si el userData coincide con el texto visible, lo usa (eligió de la
        lista); si no (tipeó a mano), parsea el número del inicio del texto.
        Lanza ValueError si no hay número válido.
        """
        texto = self.combo_codigo.currentText().strip()
        data = self.combo_codigo.currentData()
        
        if data is not None and texto.startswith(str(data)):
            return int(data)
        
        primer_token = texto.split(" ")[0].split("—")[0].strip()
        return int(primer_token)
    
    def _guardar_pago(self):
        """Guarda un nuevo pago en la base de datos."""
        
        # Validar campos obligatorios
        if not self.combo_codigo.currentText().strip():
            QMessageBox.warning(self, "Validación", "Por favor ingrese el código de cuenta.")
            return
        
        if self.input_monto.value() <= 0:
            QMessageBox.warning(self, "Validación", "El monto debe ser mayor a cero.")
            return
        
        try:
            if not BD_DISPONIBLE:
                QMessageBox.information(self, "Éxito", 
                    "Pago registrado exitosamente (modo prueba sin BD)")
                self._limpiar_formulario()
                return
            
            # Obtener el código de forma robusta (ver _resolver_codigo).
            codigo = self._resolver_codigo()
            
            # Crear movimiento
            crear_movimiento(
                codigo=codigo,
                monto=self.input_monto.value(),
                comprobante=self.input_comprobante.text(),
                descripcion=self.input_descripcion.text(),
                fecha=self.input_fecha.date().toPython(),
                usuario_id=1,  # TODO: Obtener usuario actual
                confirmar=True
            )
            
            QMessageBox.information(self, "Éxito", "Pago registrado exitosamente")
            self._limpiar_formulario()
            self._actualizar_tabla()
            
        except ValueError:
            QMessageBox.critical(self, "Error", "El código debe ser un número válido.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el pago: {str(e)}")
    
    def _limpiar_formulario(self):
        """Limpia todos los campos del formulario."""
        self.combo_codigo.setCurrentIndex(0)
        self.input_fecha.setDate(QDate.currentDate())
        self.input_comprobante.clear()
        self.input_monto.setValue(0.0)
        self.input_descripcion.clear()
    
    def _actualizar_tabla(self):
        """Actualiza la tabla con los últimos pagos."""
        
        self.tabla_pagos.setRowCount(0)
        
        if not BD_DISPONIBLE:
            self._mostrar_datos_prueba_tabla()
            return
        
        try:
            # Obtener movimientos de tipo pago
            movimientos = movimientos_detallados(
                filtro_tipo="pago",
                limite=50  # Últimos 50
            )
            
            # Llenar tabla
            for idx, mov in enumerate(movimientos):
                self.tabla_pagos.insertRow(idx)
                
                # Fecha
                item_fecha = QTableWidgetItem(str(mov.get("fecha", "")))
                self.tabla_pagos.setItem(idx, 0, item_fecha)
                
                # Código
                item_codigo = QTableWidgetItem(str(mov.get("codigo", "")))
                self.tabla_pagos.setItem(idx, 1, item_codigo)
                
                # Comprobante
                item_comprobante = QTableWidgetItem(mov.get("comprobante", ""))
                self.tabla_pagos.setItem(idx, 2, item_comprobante)
                
                # Monto (rojo)
                monto = float(mov.get("egresos", 0))
                item_monto = QTableWidgetItem(f"${monto:,.2f}")
                item_monto.setForeground(QColor("#ea4335"))
                self.tabla_pagos.setItem(idx, 3, item_monto)
                
                # Usuario
                item_usuario = QTableWidgetItem(mov.get("usuario", ""))
                self.tabla_pagos.setItem(idx, 4, item_usuario)
                
                # Estado
                estado = "✓ Activo" if not mov.get("anulado") else "✗ Anulado"
                item_estado = QTableWidgetItem(estado)
                self.tabla_pagos.setItem(idx, 5, item_estado)
            
            # Ajustar ancho de columnas
            self.tabla_pagos.resizeColumnsToContents()
            
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar los pagos: {e}")
            self._mostrar_datos_prueba_tabla()
    
    def _mostrar_datos_prueba_tabla(self):
        """Muestra datos de prueba en la tabla."""
        
        datos_prueba = [
            ("2026-01-15", "2010001", "FC 0009-00002632", 2500000.00, "Sistema", "✓ Activo"),
            ("2026-01-14", "2020001", "TR 0001-00000001", 50000000.00, "Sistema", "✓ Activo"),
            ("2026-01-13", "2030001", "FC 0010-00000001", 1500000.00, "Sistema", "✓ Activo"),
            ("2026-01-12", "2040001", "AFC - Enero", 35000000.00, "Sistema", "✓ Activo"),
            ("2026-01-11", "2010002", "FC 0009-00002631", 800000.00, "Sistema", "✓ Activo"),
        ]
        
        for idx, (fecha, cod, comp, monto, usr, estado) in enumerate(datos_prueba):
            self.tabla_pagos.insertRow(idx)
            
            self.tabla_pagos.setItem(idx, 0, QTableWidgetItem(fecha))
            self.tabla_pagos.setItem(idx, 1, QTableWidgetItem(cod))
            self.tabla_pagos.setItem(idx, 2, QTableWidgetItem(comp))
            
            item_monto = QTableWidgetItem(f"${monto:,.2f}")
            item_monto.setForeground(QColor("#ea4335"))
            self.tabla_pagos.setItem(idx, 3, item_monto)
            
            self.tabla_pagos.setItem(idx, 4, QTableWidgetItem(usr))
            self.tabla_pagos.setItem(idx, 5, QTableWidgetItem(estado))
    
    def closeEvent(self, event):
        """Detiene el timer al cerrar la pantalla."""
        self.timer.stop()
        super().closeEvent(event)


def main():
    """Función principal para pruebas."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    ventana = PantallaPagos()
    ventana.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
