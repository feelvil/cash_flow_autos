"""
panel_jerarquia.py
==================
Componente reutilizable que muestra, en vivo, la clasificación de un código de
cuenta: Partida · Sub-Partida · Detalle · Automotriz.

La idea es replicar lo que en el Excel se ve al lado del código: cuando el
usuario elige (o tipea) un código en Cobros/Pagos, este panel se actualiza y
muestra a qué corresponde ese código, para confirmar visualmente que es el
correcto antes de cargar el movimiento.

Se apoya en catalogos.buscar_por_codigo(codigo), que devuelve un CodigoCuenta
(o None si el código no existe).

Uso desde una pantalla:
    self.panel_jerarquia = PanelJerarquia()
    layout.addWidget(self.panel_jerarquia)
    # y cuando cambia el combo:
    self.panel_jerarquia.mostrar_codigo(1041131)   # o .limpiar()
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Importar la búsqueda de catálogo (con fallback si no está la BD)
try:
    from app.logica.catalogos import buscar_por_codigo
    BD_DISPONIBLE = True
except ImportError:
    BD_DISPONIBLE = False


class _Chip(QFrame):
    """
    Un "chip" visual: una etiqueta chica arriba (el nivel de la jerarquía) y el
    valor abajo. Ej:  SUB-PARTIDA / Rentas.
    
    Se usa uno por cada nivel de la clasificación.
    """
    
    def __init__(self, titulo: str, color_borde: str = "#1a73e8"):
        super().__init__()
        self._color_borde = color_borde
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #f8f9fa;
                border: 1px solid #e8eaed;
                border-left: 3px solid {color_borde};
                border-radius: 6px;
                padding: 6px 10px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        # Título del nivel (ej: "SUB-PARTIDA")
        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setStyleSheet(
            "color: #9aa0a6; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;"
        )
        layout.addWidget(self.lbl_titulo)
        
        # Valor (ej: "Rentas") — arranca vacío con un guión.
        self.lbl_valor = QLabel("—")
        self.lbl_valor.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: 500;")
        self.lbl_valor.setWordWrap(True)
        layout.addWidget(self.lbl_valor)
    
    def set_valor(self, texto: str):
        """Actualiza el valor mostrado (si viene vacío, muestra un guión)."""
        self.lbl_valor.setText(texto if texto else "—")


class PanelJerarquia(QWidget):
    """
    Fila de chips que muestra la clasificación completa de un código de cuenta.
    
    Estados:
      - Vacío / código no elegido  -> chips con "—" y un texto tenue de ayuda.
      - Código válido              -> chips con Partida, Sub-Partida, Detalle,
                                       Automotriz.
      - Código inexistente         -> mensaje "código no encontrado".
    """
    
    def __init__(self):
        super().__init__()
        self._crear_ui()
    
    def _crear_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Un chip por nivel de la jerarquía. Colores suaves para diferenciarlos.
        self.chip_partida = _Chip("PARTIDA", "#1a73e8")
        self.chip_sub_partida = _Chip("SUB-PARTIDA", "#7b1fa2")
        self.chip_detalle = _Chip("DETALLE", "#00897b")
        self.chip_automotriz = _Chip("AUTOMOTRIZ", "#f57c00")
        
        layout.addWidget(self.chip_partida, 1)
        layout.addWidget(self.chip_sub_partida, 1)
        layout.addWidget(self.chip_detalle, 1)
        layout.addWidget(self.chip_automotriz, 1)
        
        # Label de estado (aparece cuando el código no existe o no hay nada).
        self.lbl_estado = QLabel("Elegí un código para ver su clasificación")
        self.lbl_estado.setStyleSheet("color: #9aa0a6; font-size: 12px; font-style: italic;")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_estado, 2)
        
        # Estado inicial: chips ocultos, solo el texto de ayuda.
        self._mostrar_chips(False)
    
    def _mostrar_chips(self, visible: bool):
        """Muestra u oculta los chips (y al revés el texto de estado)."""
        for chip in (self.chip_partida, self.chip_sub_partida,
                     self.chip_detalle, self.chip_automotriz):
            chip.setVisible(visible)
        self.lbl_estado.setVisible(not visible)
    
    def limpiar(self):
        """Vuelve al estado inicial (sin código elegido)."""
        self.lbl_estado.setText("Elegí un código para ver su clasificación")
        self._mostrar_chips(False)
    
    def mostrar_codigo(self, codigo):
        """
        Busca el código y actualiza los chips con su clasificación.
        
        Args:
            codigo: el código numérico a mostrar. Si es None o no se puede
                    convertir a int, limpia el panel.
        """
        # Sin código válido -> limpiar.
        if codigo is None or codigo == "":
            self.limpiar()
            return
        
        try:
            codigo = int(codigo)
        except (ValueError, TypeError):
            self.limpiar()
            return
        
        # Sin BD (modo desarrollo) -> avisar sin romper.
        if not BD_DISPONIBLE:
            self.lbl_estado.setText(f"Código {codigo} (sin BD para ver la clasificación)")
            self._mostrar_chips(False)
            return
        
        try:
            info = buscar_por_codigo(codigo)
        except Exception as e:
            print(f"[DEBUG] Error buscando código {codigo}: {e}")
            self.lbl_estado.setText("No se pudo consultar la clasificación")
            self._mostrar_chips(False)
            return
        
        if info is None:
            # El código no existe en el plan de cuentas.
            self.lbl_estado.setText(f"⚠️  El código {codigo} no existe en el plan de cuentas")
            self.lbl_estado.setStyleSheet(
                "color: #f57c00; font-size: 12px; font-weight: 600;"
            )
            self._mostrar_chips(False)
            return
        
        # Código válido: llenar los chips.
        self.chip_partida.set_valor(info.partida)
        self.chip_sub_partida.set_valor(info.sub_partida)
        self.chip_detalle.set_valor(info.detalle)
        self.chip_automotriz.set_valor(info.automotriz or "Transversal")
        self._mostrar_chips(True)


# ---------------------------------------------------------------------------
# Prueba visual rápida:  py -m app.ui.panel_jerarquia
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QVBoxLayout as VB, QPushButton
    import sys
    
    app = QApplication(sys.argv)
    cont = QWidget()
    vb = VB(cont)
    
    panel = PanelJerarquia()
    vb.addWidget(panel)
    
    # Botones para probar los distintos estados
    b1 = QPushButton("Mostrar código 1041131")
    b1.clicked.connect(lambda: panel.mostrar_codigo(1041131))
    vb.addWidget(b1)
    
    b2 = QPushButton("Código inexistente (9999999)")
    b2.clicked.connect(lambda: panel.mostrar_codigo(9999999))
    vb.addWidget(b2)
    
    b3 = QPushButton("Limpiar")
    b3.clicked.connect(panel.limpiar)
    vb.addWidget(b3)
    
    cont.resize(700, 200)
    cont.show()
    sys.exit(app.exec())
