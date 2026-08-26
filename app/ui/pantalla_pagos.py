"""
Pantalla de Pagos: registrar egresos.

Similar a pantalla_cobros, pero para egresos.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QDateEdit, QSpinBox,
    QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, QDate

from app.logica.movimientos import crear_movimiento, ErrorDeNegocio
from app.logica.catalogos import listar_codigos_con_detalle
from app.logica import sesion


class PantallaPagos(QWidget):
    """
    Pantalla para registrar pagos (egresos).
    
    Estructura y flujo similares a PantallaCobros, pero para egresos.
    """
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Título
        titulo = QLabel("Registro de Pagos")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(titulo)
        
        # Formulario
        layout_form = self._crear_formulario()
        layout.addLayout(layout_form)
        
        # Tabla de referencia
        layout.addWidget(QLabel("Últimos pagos"))
        self.tabla_referencia = self._crear_tabla_referencia()
        layout.addWidget(self.tabla_referencia)
        
        self._cargar_referencias()
    
    def _crear_formulario(self) -> QVBoxLayout:
        """Crear formulario para registrar pago."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Código
        layout.addWidget(QLabel("Código de plan de cuentas"))
        self.combo_codigo = QComboBox()
        codigos = listar_codigos_con_detalle()
        for cod_info in codigos:
            self.combo_codigo.addItem(
                f"{cod_info['codigo']} - {cod_info['detalle']}",
                cod_info['codigo']
            )
        layout.addWidget(self.combo_codigo)
        
        # Fecha y monto
        layout_fila1 = QHBoxLayout()
        layout_fila1.setSpacing(12)
        
        layout_fila1.addWidget(QLabel("Fecha"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout_fila1.addWidget(self.input_fecha)
        
        layout_fila1.addWidget(QLabel("Monto"))
        self.input_monto = QSpinBox()
        self.input_monto.setMaximum(999999999)
        self.input_monto.setPrefix("$")
        layout_fila1.addWidget(self.input_monto)
        
        layout_fila1.addStretch()
        layout.addLayout(layout_fila1)
        
        # Comprobante
        layout_fila2 = QHBoxLayout()
        layout_fila2.setSpacing(12)
        
        layout_fila2.addWidget(QLabel("Comprobante (opcional)"))
        self.input_comprobante = QLineEdit()
        self.input_comprobante.setPlaceholderText("Ej: FC 001-000234")
        layout_fila2.addWidget(self.input_comprobante)
        
        layout_fila2.addStretch()
        layout.addLayout(layout_fila2)
        
        # Botón guardar
        layout_botones = QHBoxLayout()
        
        btn_guardar = QPushButton("Guardar pago")
        btn_guardar.setStyleSheet(
            """
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            """
        )
        btn_guardar.clicked.connect(self._guardar_pago)
        
        layout_botones.addStretch()
        layout_botones.addWidget(btn_guardar)
        layout.addLayout(layout_botones)
        
        return layout
    
    def _crear_tabla_referencia(self) -> QTableWidget:
        """Crear tabla con últimos pagos."""
        tabla = QTableWidget()
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["Fecha", "Código", "Comprobante", "Monto"])
        
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        tabla.setMaximumHeight(250)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        
        return tabla
    
    def _cargar_referencias(self):
        """Cargar últimos pagos en la tabla."""
        # TODO: implementar carga
        pass
    
    def _guardar_pago(self):
        """Guardar el pago en BD."""
        try:
            codigo = self.combo_codigo.currentData()
            fecha = self.input_fecha.date().toPython()
            monto = self.input_monto.value()
            comprobante = self.input_comprobante.text() or None
            
            if not codigo:
                QMessageBox.warning(self, "Error", "Selecciona un código")
                return
            
            if monto <= 0:
                QMessageBox.warning(self, "Error", "El monto debe ser mayor a 0")
                return
            
            usuario_id = sesion.usuario_actual_id()
            
            from app.database.conexion import SessionLocal
            with SessionLocal() as sesion_bd:
                crear_movimiento(
                    sesion_bd,
                    codigo=codigo,
                    fecha=fecha,
                    monto=monto,
                    usuario_id=usuario_id,
                    comprobante=comprobante
                )
            
            QMessageBox.information(
                self,
                "Éxito",
                f"Pago registrado: ${monto:,.2f}"
            )
            
            self.input_monto.setValue(0)
            self.input_comprobante.clear()
            self.input_fecha.setDate(QDate.currentDate())
            self._cargar_referencias()
        
        except ErrorDeNegocio as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
