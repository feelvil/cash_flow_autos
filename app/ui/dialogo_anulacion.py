"""
dialogo_anulacion.py
====================
Diálogo modal para anular un movimiento, reutilizable desde cualquier pantalla
(Cobros, Pagos, Reportes).

Qué hace:
  - Muestra los datos del movimiento a anular (para que el usuario confirme que
    es el correcto antes de tocar nada).
  - Pide un motivo opcional (queda guardado en la reversa como registro).
  - Al confirmar, llama a logica.movimientos.anular_movimiento dentro de su
    propia sesión de BD y hace commit.

Importante sobre la anulación (recordatorio de la lógica de negocio):
  NUNCA borra. Crea una reversa con los montos invertidos y marca el original
  como anulado. Ambos quedan anulado=True, así el saldo no se descuenta dos
  veces y queda todo el rastro (quién anuló y cuándo).
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Importar lógica de negocio y conexión
try:
    from app.database.conexion import SessionLocal
    from app.logica.movimientos import anular_movimiento, ErrorDeNegocio
    BD_DISPONIBLE = True
except ImportError:
    BD_DISPONIBLE = False
    # Definir ErrorDeNegocio dummy para que el except no rompa sin BD.
    class ErrorDeNegocio(Exception):
        pass


class DialogoAnulacion(QDialog):
    """Diálogo modal para confirmar la anulación de un movimiento."""
    
    def __init__(self, movimiento: dict, usuario_id: int = 1, parent=None):
        """
        Inicializa el diálogo.
        
        Args:
            movimiento: dict con los datos del movimiento (debe incluir 'id',
                        'fecha', 'codigo', 'comprobante', 'ingresos', 'egresos',
                        'partida', etc.). Es una fila de movimientos_detallados().
            usuario_id: quién está anulando (por ahora fijo en 1 = Sistema).
            parent: widget padre (para centrar el diálogo).
        """
        super().__init__(parent)
        
        self.movimiento = movimiento
        self.usuario_id = usuario_id
        # Bandera que la pantalla llamadora consulta después de exec():
        # True si la anulación se hizo, False si se canceló o falló.
        self.anulado_ok = False
        
        self.setWindowTitle("Anular Movimiento")
        self.setModal(True)
        self.setMinimumWidth(480)
        
        self._crear_ui()
    
    def _crear_ui(self):
        """Construye la interfaz del diálogo."""
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # ═════════════════════════════════════════════════════
        # Título con ícono de advertencia
        # ═════════════════════════════════════════════════════
        lbl_titulo = QLabel("⚠️  Confirmar Anulación")
        font_titulo = QFont("Segoe UI", 15)
        font_titulo.setWeight(QFont.Weight.Bold)
        lbl_titulo.setFont(font_titulo)
        layout.addWidget(lbl_titulo)
        
        # Texto explicativo
        lbl_explicacion = QLabel(
            "El movimiento no se borra: se crea una reversa que lo neutraliza y "
            "queda todo el historial registrado. Esta acción se puede rastrear."
        )
        lbl_explicacion.setWordWrap(True)
        lbl_explicacion.setStyleSheet("color: #5f6368; font-size: 12px;")
        layout.addWidget(lbl_explicacion)
        
        # ═════════════════════════════════════════════════════
        # Tarjeta con los datos del movimiento
        # ═════════════════════════════════════════════════════
        frame_datos = QFrame()
        frame_datos.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e8eaed;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel { border: none; background: transparent; }
        """)
        layout_datos = QVBoxLayout(frame_datos)
        layout_datos.setSpacing(6)
        
        # Armar las líneas de datos a mostrar
        m = self.movimiento
        
        # Determinar si es cobro o pago y el monto correspondiente
        ingresos = float(m.get("ingresos", 0) or 0)
        egresos = float(m.get("egresos", 0) or 0)
        if ingresos > 0:
            tipo_txt = "Cobro (ingreso)"
            monto_txt = self._formatear_moneda(ingresos)
            color_monto = "#34a853"
        else:
            tipo_txt = "Pago (egreso)"
            monto_txt = self._formatear_moneda(egresos)
            color_monto = "#ea4335"
        
        # Filas de datos (etiqueta: valor)
        filas = [
            ("Fecha:", str(m.get("fecha", ""))),
            ("Código:", str(m.get("codigo", ""))),
            ("Clasificación:", f"{m.get('sub_partida', '')} · {m.get('detalle', '')}"),
            ("Comprobante:", str(m.get("comprobante", "") or "—")),
            ("Tipo:", tipo_txt),
        ]
        
        for etiqueta, valor in filas:
            fila_layout = QHBoxLayout()
            lbl_et = QLabel(etiqueta)
            lbl_et.setStyleSheet("color: #5f6368; font-size: 12px; font-weight: 600;")
            lbl_et.setFixedWidth(110)
            lbl_val = QLabel(valor)
            lbl_val.setStyleSheet("color: #2c3e50; font-size: 12px;")
            lbl_val.setWordWrap(True)
            fila_layout.addWidget(lbl_et)
            fila_layout.addWidget(lbl_val, 1)
            layout_datos.addLayout(fila_layout)
        
        # Monto destacado (con color según tipo)
        fila_monto = QHBoxLayout()
        lbl_monto_et = QLabel("Monto:")
        lbl_monto_et.setStyleSheet("color: #5f6368; font-size: 12px; font-weight: 600;")
        lbl_monto_et.setFixedWidth(110)
        lbl_monto_val = QLabel(monto_txt)
        lbl_monto_val.setStyleSheet(
            f"color: {color_monto}; font-size: 15px; font-weight: bold;"
        )
        fila_monto.addWidget(lbl_monto_et)
        fila_monto.addWidget(lbl_monto_val, 1)
        layout_datos.addLayout(fila_monto)
        
        layout.addWidget(frame_datos)
        
        # ═════════════════════════════════════════════════════
        # Campo de motivo (opcional)
        # ═════════════════════════════════════════════════════
        lbl_motivo = QLabel("Motivo de la anulación (opcional):")
        lbl_motivo.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(lbl_motivo)
        
        self.input_motivo = QTextEdit()
        self.input_motivo.setPlaceholderText(
            "Ej: cargado por error, monto equivocado, comprobante duplicado..."
        )
        self.input_motivo.setMaximumHeight(70)
        layout.addWidget(self.input_motivo)
        
        # ═════════════════════════════════════════════════════
        # Botones
        # ═════════════════════════════════════════════════════
        layout_botones = QHBoxLayout()
        layout_botones.addStretch()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("botonSecundario")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #5f6368;
                border: 1px solid #d0d7e0;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #f8f9fa; }
        """)
        btn_cancelar.clicked.connect(self.reject)
        layout_botones.addWidget(btn_cancelar)
        
        btn_anular = QPushButton("🗑️  Anular Movimiento")
        btn_anular.setStyleSheet("""
            QPushButton {
                background-color: #ea4335;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #d33427; }
        """)
        btn_anular.clicked.connect(self._confirmar_anulacion)
        layout_botones.addWidget(btn_anular)
        
        layout.addLayout(layout_botones)
    
    def _confirmar_anulacion(self):
        """Ejecuta la anulación llamando a la lógica de negocio."""
        
        movimiento_id = self.movimiento.get("id")
        if movimiento_id is None:
            QMessageBox.critical(
                self, "Error",
                "No se pudo identificar el movimiento (falta el id)."
            )
            return
        
        motivo = self.input_motivo.toPlainText().strip() or None
        
        if not BD_DISPONIBLE:
            # Modo prueba: simular éxito sin tocar nada
            QMessageBox.information(
                self, "Anulado (modo prueba)",
                "El movimiento se habría anulado (modo prueba sin BD)."
            )
            self.anulado_ok = True
            self.accept()
            return
        
        try:
            # Abrir sesión propia y anular (la función hace commit por confirmar=True)
            with SessionLocal() as sesion:
                reversa = anular_movimiento(
                    sesion,
                    movimiento_id=movimiento_id,
                    usuario_id=self.usuario_id,
                    motivo=motivo,
                    confirmar=True,
                )
            
            QMessageBox.information(
                self, "Movimiento Anulado",
                f"El movimiento #{movimiento_id} se anuló correctamente.\n"
                f"Se generó la reversa #{reversa.id} como registro."
            )
            self.anulado_ok = True
            self.accept()
            
        except ErrorDeNegocio as e:
            # Error esperable (ej: ya estaba anulado): mensaje claro, no técnico.
            QMessageBox.warning(self, "No se puede anular", str(e))
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Ocurrió un error al anular el movimiento:\n{str(e)}"
            )
    
    @staticmethod
    def _formatear_moneda(valor: float) -> str:
        """Formatea un número como moneda argentina ($1.234.567,89)."""
        formateado = f"{valor:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
        return f"${formateado}"


def anular_movimiento_con_dialogo(movimiento: dict, usuario_id: int = 1, parent=None) -> bool:
    """
    Función de conveniencia: abre el diálogo de anulación y devuelve True si el
    movimiento se anuló, False si se canceló o falló.
    
    Uso desde una pantalla:
        if anular_movimiento_con_dialogo(fila_seleccionada, parent=self):
            self._actualizar_tabla()  # recargar para ver el cambio
    """
    dialogo = DialogoAnulacion(movimiento, usuario_id=usuario_id, parent=parent)
    dialogo.exec()
    return dialogo.anulado_ok
