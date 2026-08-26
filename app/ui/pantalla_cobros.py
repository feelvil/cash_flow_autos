"""
Pantalla de Cobros: registrar ingresos.

Elementos:
- Combo de códigos (plan de cuentas)
- Fecha del movimiento
- Comprobante
- Monto
- Botón guardar
- Tabla de referencia con últimos cobros
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QDateEdit, QSpinBox,
    QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, QDate

# Importar lógica
from app.logica.movimientos import crear_movimiento, ErrorDeNegocio
from app.logica.catalogos import listar_codigos_con_detalle
from app.logica import sesion


class PantallaCobros(QWidget):
    """
    Pantalla para registrar cobros (ingresos).
    
    Flujo:
    1. Usuario elige código (con autocompletado por nombre)
    2. Ingresa fecha y monto
    3. Ingresa número de comprobante (opcional)
    4. Clic "Guardar cobro"
    5. Se valida y guarda en BD
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
        titulo = QLabel("Registro de Cobros")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(titulo)
        
        # ========================================================================
        # FORMULARIO
        # ========================================================================
        layout_form = self._crear_formulario()
        layout.addLayout(layout_form)
        
        # ========================================================================
        # TABLA DE REFERENCIA (últimos cobros)
        # ========================================================================
        layout.addWidget(QLabel("Últimos cobros"))
        self.tabla_referencia = self._crear_tabla_referencia()
        layout.addWidget(self.tabla_referencia)
        
        # Cargar datos
        self._cargar_referencias()
    
    def _crear_formulario(self) -> QVBoxLayout:
        """
        Crear formulario para registrar cobro.
        
        Campos:
        - Código (combo con búsqueda)
        - Fecha
        - Monto
        - Comprobante
        - Botón guardar
        """
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Código
        layout.addWidget(QLabel("Código de plan de cuentas"))
        self.combo_codigo = QComboBox()
        # TODO: implementar búsqueda por palabras
        codigos = listar_codigos_con_detalle()
        for cod_info in codigos:
            self.combo_codigo.addItem(
                f"{cod_info['codigo']} - {cod_info['detalle']}",
                cod_info['codigo']
            )
        layout.addWidget(self.combo_codigo)
        
        # Fecha
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
        self.input_comprobante.setPlaceholderText("Ej: RC 0001-00072116")
        layout_fila2.addWidget(self.input_comprobante)
        
        layout_fila2.addStretch()
        layout.addLayout(layout_fila2)
        
        # Botón guardar
        layout_botones = QHBoxLayout()
        
        btn_guardar = QPushButton("Guardar cobro")
        btn_guardar.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        btn_guardar.clicked.connect(self._guardar_cobro)
        
        layout_botones.addStretch()
        layout_botones.addWidget(btn_guardar)
        layout.addLayout(layout_botones)
        
        return layout
    
    def _crear_tabla_referencia(self) -> QTableWidget:
        """
        Crear tabla con últimos cobros para referencia.
        
        Columnas:
        - Fecha
        - Código
        - Comprobante
        - Monto
        """
        tabla = QTableWidget()
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["Fecha", "Código", "Comprobante", "Monto"])
        
        # Configurar ancho
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        tabla.setMaximumHeight(250)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        
        return tabla
    
    def _cargar_referencias(self):
        """
        Cargar últimos cobros en la tabla de referencia.
        """
        # TODO: implementar carga de últimos cobros
        pass
    
    def _guardar_cobro(self):
        """
        Guardar el cobro en la BD.
        
        Validar:
        - Código válido
        - Monto > 0
        - Fecha válida
        
        Luego guardar en BD con el usuario de sesión.
        """
        try:
            # Obtener valores del formulario
            codigo = self.combo_codigo.currentData()
            fecha = self.input_fecha.date().toPython()
            monto = self.input_monto.value()
            comprobante = self.input_comprobante.text() or None
            
            # Validaciones básicas
            if not codigo:
                QMessageBox.warning(self, "Error", "Selecciona un código")
                return
            
            if monto <= 0:
                QMessageBox.warning(self, "Error", "El monto debe ser mayor a 0")
                return
            
            # Obtener usuario de sesión
            usuario_id = sesion.usuario_actual_id()
            
            # Crear movimiento en BD
            # El movimiento es un INGRESO (cobro)
            # Firma: crear_movimiento(session, *, codigo, fecha, monto, usuario_id, comprobante=None, descripcion=None)
            # Para diferenciar si es ingreso o egreso, el código lo determina via plan de cuentas
            
            # Por ahora, asumimos que la lógica de movimientos.py determina
            # si es ingreso o egreso según el código
            
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
            
            # Mostrar éxito
            QMessageBox.information(
                self,
                "Éxito",
                f"Cobro registrado: ${monto:,.2f}"
            )
            
            # Limpiar formulario
            self.input_monto.setValue(0)
            self.input_comprobante.clear()
            self.input_fecha.setDate(QDate.currentDate())
            
            # Recargar tabla de referencia
            self._cargar_referencias()
        
        except ErrorDeNegocio as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
