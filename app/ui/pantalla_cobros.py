"""
CASH FLOW AUTOS — Pantalla de Cobros
====================================

Pantalla para registrar cobros (ingresos).

Estructura:
- Formulario de carga (código, comprobante, monto, descripción)
- Tabla de últimos cobros registrados
- Validaciones y manejo de errores
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta

# Importar lógica de negocio
try:
    from app.logica.movimientos import crear_movimiento
    from app.logica.reportes import movimientos_detallados
    from app.logica.catalogos import obtener_codigos_cobro
    BD_DISPONIBLE = True
except ImportError:
    BD_DISPONIBLE = False

# El panel de jerarquía se importa aparte: sabe manejar el caso sin BD por sí
# mismo, así que queremos que esté disponible aunque la lógica no cargue.
try:
    from app.ui.panel_jerarquia import PanelJerarquia
except ImportError:
    PanelJerarquia = None

# Completer con búsqueda por palabras (nombre o número) para el combo de códigos.
try:
    from app.ui.completer_codigos import instalar_completer_palabras
except ImportError:
    instalar_completer_palabras = None


# Códigos de respaldo si la BD no está disponible (modo prueba / sin conexión).
# La etiqueta es solo ilustrativa; los reales vienen de catalogos.obtener_codigos_cobro().
CODIGOS_PRUEBA_COBRO = [
    "1041131 — Rentas · NEUQUÉN 1° Q",
    "1041132 — Rentas · CORRIENTES 1° Q",
    "1041133 — Rentas · MISIONES",
    "1045451 — Registración",
    "1050001 — Entidades co-participadas",
]


class PantallaCobros(QWidget):
    """Pantalla para registrar cobros (ingresos)."""
    
    def __init__(self):
        """Inicializa la pantalla de cobros."""
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
        lbl_titulo_form = QLabel("Registrar Nuevo Cobro")
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
        # Permite tipear y que el combo filtre las coincidencias.
        self.combo_codigo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._cargar_codigos()  # llena el combo con datos reales (o de prueba)
        # Instalar la búsqueda por palabras (nombre o número). Va DESPUÉS de
        # llenar el combo, porque el completer toma el modelo ya poblado.
        if instalar_completer_palabras is not None:
            instalar_completer_palabras(self.combo_codigo)
        layout_f1.addWidget(self.combo_codigo, 1)
        
        # Fecha
        layout_f1.addWidget(QLabel("Fecha:"))
        self.input_fecha = QDateEdit()
        self.input_fecha.setDate(QDate.currentDate())
        self.input_fecha.setCalendarPopup(True)
        layout_f1.addWidget(self.input_fecha)
        
        layout_form.addLayout(layout_f1)
        
        # ═════════════════════════════════════════════════════
        # PANEL DE JERARQUÍA (se actualiza al elegir/tipear un código)
        # ═════════════════════════════════════════════════════
        # Muestra la clasificación del código elegido (Partida · Sub-Partida ·
        # Detalle · Automotriz), como referencia visual antes de cargar.
        if PanelJerarquia is not None:
            self.panel_jerarquia = PanelJerarquia()
            layout_form.addWidget(self.panel_jerarquia)
        else:
            self.panel_jerarquia = None
        
        # Timer con debounce: al tipear en el combo se disparan muchas señales.
        # En vez de consultar la BD en cada tecla, esperamos 300 ms de "silencio"
        # y recién ahí buscamos la clasificación. Más suave para la BD y la UI.
        self._timer_jerarquia = QTimer()
        self._timer_jerarquia.setSingleShot(True)
        self._timer_jerarquia.setInterval(300)
        self._timer_jerarquia.timeout.connect(self._actualizar_jerarquia)
        
        # Conectar los cambios del combo (elegir de la lista o tipear) al timer.
        self.combo_codigo.currentIndexChanged.connect(self._programar_jerarquia)
        self.combo_codigo.editTextChanged.connect(self._programar_jerarquia)
        
        # Mostrar la jerarquía del código inicial (el primero del combo).
        self._actualizar_jerarquia()
        
        # ═════════════════════════════════════════════════════
        # FILA 2: Comprobante y Monto
        # ═════════════════════════════════════════════════════
        layout_f2 = QHBoxLayout()
        layout_f2.setSpacing(12)
        
        # Comprobante
        layout_f2.addWidget(QLabel("Comprobante:"))
        self.input_comprobante = QLineEdit()
        self.input_comprobante.setPlaceholderText("Ej: RC 0001-00072116")
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
        
        btn_guardar = QPushButton("💾 Guardar Cobro")
        btn_guardar.setObjectName("botonExito")
        btn_guardar.clicked.connect(self._guardar_cobro)
        layout_f4.addWidget(btn_guardar)
        
        btn_limpiar = QPushButton("🗑️  Limpiar")
        btn_limpiar.setObjectName("botonSecundario")
        btn_limpiar.clicked.connect(self._limpiar_formulario)
        layout_f4.addWidget(btn_limpiar)
        
        layout_f4.addStretch()
        
        layout_form.addLayout(layout_f4)
        
        layout_principal.addWidget(frame_form)
        
        # ═════════════════════════════════════════════════════
        # SECCIÓN 2: TABLA DE ÚLTIMOS COBROS
        # ═════════════════════════════════════════════════════
        
        lbl_titulo_tabla = QLabel("Últimos Cobros Registrados")
        font_titulo = QFont("Segoe UI", 14)
        font_titulo.setWeight(QFont.Weight.Bold)
        lbl_titulo_tabla.setFont(font_titulo)
        layout_principal.addWidget(lbl_titulo_tabla)
        
        # Tabla
        self.tabla_cobros = QTableWidget()
        self.tabla_cobros.setColumnCount(6)
        self.tabla_cobros.setHorizontalHeaderLabels([
            "Fecha", "Código", "Comprobante", "Monto", "Usuario", "Estado"
        ])
        self.tabla_cobros.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_cobros.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_cobros.setAlternatingRowColors(True)
        self.tabla_cobros.setMinimumHeight(200)
        
        # Estilos de tabla
        self.tabla_cobros.setStyleSheet("""
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
                background-color: #e3f2fd;
                color: #1a73e8;
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
        
        layout_principal.addWidget(self.tabla_cobros, 1)  # Tomar espacio flexible
    
    def _cargar_codigos(self):
        """
        Llena el combo de códigos con datos reales de la BD (partidas INGRESOS).
        
        Cada item guarda:
          - Texto visible: la etiqueta linda (ej: "1041131 — Rentas · NEUQUÉN")
          - Dato oculto (userData): el código numérico (ej: 1041131), que es lo
            que después usamos al guardar, sin tener que parsear el texto.
        
        Si la BD no está disponible, cae a una lista de prueba para que la
        pantalla siga siendo usable en desarrollo.
        """
        self.combo_codigo.clear()
        
        if not BD_DISPONIBLE:
            self.combo_codigo.addItems(CODIGOS_PRUEBA_COBRO)
            return
        
        try:
            codigos = obtener_codigos_cobro()
            if not codigos:
                # La BD respondió pero no hay códigos de ingreso: usar prueba.
                self.combo_codigo.addItems(CODIGOS_PRUEBA_COBRO)
                return
            
            for c in codigos:
                # addItem(texto, userData) -> guardamos el código numérico como dato.
                self.combo_codigo.addItem(c.etiqueta(), userData=c.codigo)
                
        except Exception as e:
            print(f"[DEBUG] No se pudieron cargar códigos de la BD: {e}")
            self.combo_codigo.addItems(CODIGOS_PRUEBA_COBRO)
    
    def _programar_jerarquia(self, *args):
        """
        Reinicia el timer de debounce. Se llama en cada cambio del combo; el
        timer, tras 300 ms sin cambios, dispara _actualizar_jerarquia.
        """
        if self.panel_jerarquia is not None:
            self._timer_jerarquia.start()
    
    def _actualizar_jerarquia(self):
        """
        Busca la clasificación del código actual y la muestra en el panel.
        Reutiliza _resolver_codigo para obtener el número; si no hay número
        válido (combo vacío o texto incompleto), limpia el panel.
        """
        if self.panel_jerarquia is None:
            return
        try:
            codigo = self._resolver_codigo()
        except (ValueError, AttributeError):
            self.panel_jerarquia.limpiar()
            return
        self.panel_jerarquia.mostrar_codigo(codigo)
    
    def _resolver_codigo(self) -> int:
        """
        Devuelve el código numérico elegido en el combo.
        
        Prioridad:
          1. Si el userData (código guardado) coincide con el texto visible,
             lo usamos tal cual (caso normal: el usuario eligió de la lista).
          2. Si no coincide (el usuario tipeó a mano), parseamos el número del
             principio del texto.
        
        Lanza ValueError si no se puede obtener un número válido (lo captura
        _guardar_cobro para avisar al usuario).
        """
        texto = self.combo_codigo.currentText().strip()
        data = self.combo_codigo.currentData()
        
        # Caso 1: el dato oculto es válido y el texto empieza con ese código.
        if data is not None and texto.startswith(str(data)):
            return int(data)
        
        # Caso 2: parsear del texto (ej: "1041131 — Rentas · ...").
        primer_token = texto.split(" ")[0].split("—")[0].strip()
        return int(primer_token)
    
    def _guardar_cobro(self):
        """Guarda un nuevo cobro en la base de datos."""
        
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
                    "Cobro registrado exitosamente (modo prueba sin BD)")
                self._limpiar_formulario()
                return
            
            # Obtener el código de forma robusta. Ojo con el combo editable:
            # si el usuario TIPEA a mano, Qt puede dejar currentData() apuntando
            # al último item que coincidía, aunque el texto ya no sea ese. Por eso
            # sólo confiamos en userData si su código aparece al inicio del texto
            # visible; si no, parseamos el número directo del texto tipeado.
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
            
            QMessageBox.information(self, "Éxito", "Cobro registrado exitosamente")
            self._limpiar_formulario()
            self._actualizar_tabla()
            
        except ValueError:
            QMessageBox.critical(self, "Error", "El código debe ser un número válido.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el cobro: {str(e)}")
    
    def _limpiar_formulario(self):
        """Limpia todos los campos del formulario."""
        self.combo_codigo.setCurrentIndex(0)
        self.input_fecha.setDate(QDate.currentDate())
        self.input_comprobante.clear()
        self.input_monto.setValue(0.0)
        self.input_descripcion.clear()
    
    def _actualizar_tabla(self):
        """Actualiza la tabla con los últimos cobros."""
        
        self.tabla_cobros.setRowCount(0)
        
        # Siempre mostrar datos de prueba si BD no disponible
        if not BD_DISPONIBLE:
            self._mostrar_datos_prueba_tabla()
            return
        
        try:
            # Obtener movimientos de tipo cobro
            movimientos = movimientos_detallados()
            
            if not movimientos:
                self._mostrar_datos_prueba_tabla()
                return
            
            # Llenar tabla
            for idx, mov in enumerate(movimientos):
                self.tabla_cobros.insertRow(idx)
                
                # Fecha — en esta primera celda guardamos, oculto, el dict
                # completo del movimiento (Qt.UserRole). Así, al anular, sabemos
                # exactamente qué fila es sin re-consultar la BD.
                item_fecha = QTableWidgetItem(str(mov.get("fecha", "")))
                item_fecha.setData(Qt.ItemDataRole.UserRole, mov)
                self.tabla_cobros.setItem(idx, 0, item_fecha)
                
                # Código
                item_codigo = QTableWidgetItem(str(mov.get("codigo", "")))
                self.tabla_cobros.setItem(idx, 1, item_codigo)
                
                # Comprobante
                item_comprobante = QTableWidgetItem(str(mov.get("comprobante", "")))
                self.tabla_cobros.setItem(idx, 2, item_comprobante)
                
                # Monto (verde)
                try:
                    monto = float(mov.get("ingresos", 0))
                    item_monto = QTableWidgetItem(f"${monto:,.2f}")
                    item_monto.setForeground(QColor("#34a853"))
                except:
                    item_monto = QTableWidgetItem("$0,00")
                self.tabla_cobros.setItem(idx, 3, item_monto)
                
                # Usuario
                item_usuario = QTableWidgetItem(str(mov.get("usuario", "")))
                self.tabla_cobros.setItem(idx, 4, item_usuario)
                
                # Estado
                anulado = bool(mov.get("anulado"))
                estado = "✗ Anulado" if anulado else "✓ Activo"
                item_estado = QTableWidgetItem(estado)
                if anulado:
                    # Fila anulada: texto gris y tachado para distinguirla visualmente.
                    item_estado.setForeground(QColor("#9aa0a6"))
                self.tabla_cobros.setItem(idx, 5, item_estado)
                
                # Si está anulado, atenuar toda la fila.
                if anulado:
                    for col in range(6):
                        it = self.tabla_cobros.item(idx, col)
                        if it:
                            fuente = it.font()
                            fuente.setStrikeOut(True)
                            it.setFont(fuente)
                            it.setForeground(QColor("#9aa0a6"))
            
            # Ajustar ancho de columnas
            self.tabla_cobros.resizeColumnsToContents()
            
        except Exception as e:
            print(f"[DEBUG] Cargando datos de prueba en Cobros: {e}")
            self._mostrar_datos_prueba_tabla()
    
    def _mostrar_datos_prueba_tabla(self):
        """Muestra datos de prueba en la tabla."""
        
        datos_prueba = [
            ("2026-01-15", "1041131", "RC 0001-00072116", 17531900.00, "Sistema", "✓ Activo"),
            ("2026-01-14", "1045451", "FC 0009-00002632", 2500000.00, "Sistema", "✓ Activo"),
            ("2026-01-13", "1041132", "RC 0001-00072115", 5000000.00, "Sistema", "✓ Activo"),
            ("2026-01-12", "1041133", "RC 0001-00072114", 1250000.00, "Sistema", "✓ Activo"),
            ("2026-01-11", "1050001", "TR 0001-00000001", 10000000.00, "Sistema", "✓ Activo"),
        ]
        
        for idx, (fecha, cod, comp, monto, usr, estado) in enumerate(datos_prueba):
            self.tabla_cobros.insertRow(idx)
            
            self.tabla_cobros.setItem(idx, 0, QTableWidgetItem(fecha))
            self.tabla_cobros.setItem(idx, 1, QTableWidgetItem(cod))
            self.tabla_cobros.setItem(idx, 2, QTableWidgetItem(comp))
            
            item_monto = QTableWidgetItem(f"${monto:,.2f}")
            item_monto.setForeground(QColor("#34a853"))
            self.tabla_cobros.setItem(idx, 3, item_monto)
            
            self.tabla_cobros.setItem(idx, 4, QTableWidgetItem(usr))
            self.tabla_cobros.setItem(idx, 5, QTableWidgetItem(estado))
    
    def closeEvent(self, event):
        """Detiene el timer al cerrar la pantalla."""
        self.timer.stop()
        super().closeEvent(event)


def main():
    """Función principal para pruebas."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    ventana = PantallaCobros()
    ventana.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
