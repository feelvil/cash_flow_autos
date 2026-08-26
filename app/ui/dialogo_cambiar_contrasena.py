"""
Diálogo para cambiar la contraseña del usuario.

Flujo:
1. Usuario ingresa contraseña actual (validación)
2. Ingresa contraseña nueva (dos veces)
3. Si todo es válido, actualizar en BD
4. Mostrar mensaje de éxito o error
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QWidget
)
from PySide6.QtCore import Qt

# Importar funciones de autenticación y sesión
from app.logica.auth import cambiar_password, ErrorDeNegocio
from app.logica import sesion


class DialogoCambiarContrasena(QDialog):
    """
    Diálogo modal para cambiar la contraseña del usuario.
    
    Elementos:
    - Campo contraseña actual (validación obligatoria)
    - Campo contraseña nueva
    - Campo repetir contraseña nueva
    - Botones Aceptar / Cancelar
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración del diálogo
        self.setWindowTitle("Cambiar contraseña")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Crear layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # ========================================================================
        # INSTRUCCIÓN
        # ========================================================================
        label_instruccion = QLabel(
            "Ingresa tu contraseña actual y define una nueva contraseña."
        )
        label_instruccion.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(label_instruccion)
        
        # ========================================================================
        # CONTRASEÑA ACTUAL
        # ========================================================================
        layout.addWidget(QLabel("Contraseña actual"))
        self.input_actual = QLineEdit()
        self.input_actual.setEchoMode(QLineEdit.Password)
        self.input_actual.setPlaceholderText("Ingresa tu contraseña actual")
        layout.addWidget(self.input_actual)
        
        # ========================================================================
        # CONTRASEÑA NUEVA
        # ========================================================================
        layout.addWidget(QLabel("Contraseña nueva"))
        self.input_nueva = QLineEdit()
        self.input_nueva.setEchoMode(QLineEdit.Password)
        self.input_nueva.setPlaceholderText("Define una contraseña nueva")
        layout.addWidget(self.input_nueva)
        
        # ========================================================================
        # REPETIR CONTRASEÑA NUEVA
        # ========================================================================
        layout.addWidget(QLabel("Repetir contraseña nueva"))
        self.input_repetir = QLineEdit()
        self.input_repetir.setEchoMode(QLineEdit.Password)
        self.input_repetir.setPlaceholderText("Repite la contraseña nueva")
        layout.addWidget(self.input_repetir)
        
        # Agregar spacer vertical
        layout.addSpacing(8)
        
        # Mensaje de validación (inicialmente oculto)
        self.label_error = QLabel("")
        self.label_error.setStyleSheet("color: #d32f2f; font-size: 12px;")
        self.label_error.setVisible(False)
        layout.addWidget(self.label_error)
        
        layout.addStretch()
        
        # ========================================================================
        # BOTONES
        # ========================================================================
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(8)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        
        btn_aceptar = QPushButton("Cambiar contraseña")
        btn_aceptar.setStyleSheet(
            "background-color: #4CAF50; color: white; border: none; "
            "padding: 6px 16px; border-radius: 4px; font-weight: bold;"
        )
        btn_aceptar.clicked.connect(self._cambiar_contrasena)
        
        layout_botones.addStretch()
        layout_botones.addWidget(btn_cancelar)
        layout_botones.addWidget(btn_aceptar)
        
        layout.addLayout(layout_botones)
        
        # Permitir enviar con Enter en el último campo
        self.input_repetir.returnPressed.connect(self._cambiar_contrasena)
    
    def _validar_campos(self) -> tuple[bool, str]:
        """
        Validar que los campos de entrada sean correctos.
        
        Retorna:
            tuple: (es_válido: bool, mensaje_error: str)
        """
        # Contraseña actual no debe estar vacía
        if not self.input_actual.text():
            return False, "Ingresa tu contraseña actual"
        
        # Contraseña nueva no debe estar vacía
        if not self.input_nueva.text():
            return False, "Define una contraseña nueva"
        
        # Contraseña nueva debe tener al menos 6 caracteres (mínimo recomendado)
        if len(self.input_nueva.text()) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"
        
        # Las dos contraseñas nuevas deben coincidir
        if self.input_nueva.text() != self.input_repetir.text():
            return False, "Las contraseñas nuevas no coinciden"
        
        # Contraseña nueva no puede ser igual a la actual
        if self.input_actual.text() == self.input_nueva.text():
            return False, "La contraseña nueva debe ser diferente a la actual"
        
        return True, ""
    
    def _cambiar_contrasena(self):
        """
        Procesar el cambio de contraseña.
        
        Flujo:
        1. Validar campos localmente
        2. Verificar contraseña actual en la BD
        3. Cambiar contraseña en la BD (con bcrypt)
        4. Mostrar resultado (éxito o error)
        """
        # Validar campos
        es_valido, mensaje_error = self._validar_campos()
        
        if not es_valido:
            # Mostrar error y retornar
            self.label_error.setText(mensaje_error)
            self.label_error.setVisible(True)
            return
        
        # Ocultar error si estaba visible (nueva validación correcta)
        self.label_error.setVisible(False)
        
        try:
            # Obtener el ID del usuario actual
            usuario_id = sesion.usuario_actual_id()
            
            # Llamar a la función de cambio de contraseña
            # Firma: cambiar_password(usuario_id, password_actual, password_nueva)
            cambiar_password(
                usuario_id,
                self.input_actual.text(),
                self.input_nueva.text()
            )
            
            # Si llegó aquí, el cambio fue exitoso
            QMessageBox.information(
                self,
                "Éxito",
                "Tu contraseña ha sido actualizada correctamente."
            )
            
            # Cerrar el diálogo
            self.accept()
        
        except ErrorDeNegocio as e:
            # Error de negocio (ej: contraseña actual incorrecta)
            self.label_error.setText(str(e))
            self.label_error.setVisible(True)
        
        except Exception as e:
            # Error inesperado
            QMessageBox.critical(
                self,
                "Error",
                f"Ocurrió un error al cambiar la contraseña:\n{str(e)}"
            )
