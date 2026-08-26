"""
Pantalla de login: autenticación de usuario.

Elementos:
- Combo con lista de usuarios activos
- Campo de contraseña
- Botones Ingresar / Cancelar
- Validación de credenciales con bcrypt
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

# Importar funciones de auth y sesión
from app.logica.auth import listar_usuarios_activos, verificar_login, establecer_password, ResultadoLogin
from app.logica import sesion
from app.ui.main_window import VentanaPrincipal


class VentanaLogin(QWidget):
    """
    Ventana de login principal.
    
    Flujo:
    1. Usuario elige su nombre en el combo
    2. Ingresa contraseña (o define si es primer ingreso)
    3. Clic "Ingresar"
    4. Si OK, abre VentanaPrincipal y cierra login
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Cash Flow Autos — Login")
        self.setGeometry(400, 200, 400, 300)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ========================================================================
        # TÍTULO
        # ========================================================================
        titulo = QLabel("Cash Flow Autos")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2196F3;")
        layout.addWidget(titulo)
        
        layout.addWidget(QLabel("Sistema de gestión de flujo de fondos"))
        layout.addSpacing(12)
        
        # ========================================================================
        # USUARIO (combo)
        # ========================================================================
        layout.addWidget(QLabel("Usuario"))
        self.combo_usuario = QComboBox()
        
        # Cargar usuarios activos
        usuarios = listar_usuarios_activos()
        for u in usuarios:
            self.combo_usuario.addItem(u['nombre'], u['id'])
        
        layout.addWidget(self.combo_usuario)
        
        # ========================================================================
        # CONTRASEÑA
        # ========================================================================
        layout.addWidget(QLabel("Contraseña"))
        self.input_contrasena = QLineEdit()
        self.input_contrasena.setEchoMode(QLineEdit.Password)
        self.input_contrasena.setPlaceholderText("Ingresa tu contraseña")
        self.input_contrasena.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.input_contrasena)
        
        # Spacer
        layout.addSpacing(8)
        
        # Mensaje de error
        self.label_error = QLabel("")
        self.label_error.setStyleSheet("color: #d32f2f; font-size: 12px;")
        self.label_error.setVisible(False)
        layout.addWidget(self.label_error)
        
        layout.addStretch()
        
        # ========================================================================
        # BOTONES
        # ========================================================================
        layout_botones = QHBoxLayout()
        
        btn_cancelar = QPushButton("Salir")
        btn_cancelar.clicked.connect(self.close)
        
        btn_ingresar = QPushButton("Ingresar")
        btn_ingresar.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        btn_ingresar.clicked.connect(self._intentar_login)
        
        layout_botones.addStretch()
        layout_botones.addWidget(btn_cancelar)
        layout_botones.addWidget(btn_ingresar)
        layout.addLayout(layout_botones)
    
    def _intentar_login(self):
        """
        Intentar login con los datos ingresados.
        
        Flujo:
        1. Obtener usuario_id del combo
        2. Obtener contraseña del input
        3. Verificar en BD (bcrypt)
        4. Si OK, abrir VentanaPrincipal
        5. Si error, mostrar mensaje
        """
        # Limpiar error anterior
        self.label_error.setVisible(False)
        
        # Obtener datos
        usuario_id = self.combo_usuario.currentData()
        usuario_nombre = self.combo_usuario.currentText()
        password = self.input_contrasena.text()
        
        if not usuario_id:
            self.label_error.setText("Selecciona un usuario")
            self.label_error.setVisible(True)
            return
        
        if not password:
            self.label_error.setText("Ingresa tu contraseña")
            self.label_error.setVisible(True)
            return
        
        # Verificar login
        resultado = verificar_login(usuario_id, password)
        
        # Caso: usuario sin contraseña (primer ingreso)
        if resultado.necesita_password:
            self._dialogo_primera_contraseña(usuario_id, usuario_nombre)
            return
        
        # Caso: login exitoso
        if resultado.exitoso:
            # Guardar sesión
            sesion.iniciar_sesion(usuario_id, usuario_nombre)
            
            # Abrir ventana principal
            self.ventana_principal = VentanaPrincipal()
            self.ventana_principal.show()
            
            # Cerrar login
            self.close()
        
        # Caso: error (contraseña incorrecta, usuario no existe)
        else:
            self.label_error.setText(resultado.mensaje)
            self.label_error.setVisible(True)
            self.input_contrasena.clear()
    
    def _dialogo_primera_contraseña(self, usuario_id: int, usuario_nombre: str):
        """
        Diálogo para usuario sin contraseña (primer ingreso).
        
        Le pide que ingrese su contraseña por primera vez.
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
        
        # Crear diálogo
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Primera contraseña")
        dialogo.setGeometry(400, 250, 350, 200)
        
        layout = QVBoxLayout(dialogo)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        layout.addWidget(QLabel(f"Hola {usuario_nombre}!"))
        layout.addWidget(QLabel("Ingresa una contraseña para tu cuenta:"))
        
        input_nueva = QLineEdit()
        input_nueva.setEchoMode(QLineEdit.Password)
        input_nueva.setPlaceholderText("Contraseña (mín. 6 caracteres)")
        layout.addWidget(input_nueva)
        
        input_repetir = QLineEdit()
        input_repetir.setEchoMode(QLineEdit.Password)
        input_repetir.setPlaceholderText("Repetir contraseña")
        layout.addWidget(input_repetir)
        
        label_error = QLabel("")
        label_error.setStyleSheet("color: #d32f2f; font-size: 12px;")
        label_error.setVisible(False)
        layout.addWidget(label_error)
        
        layout.addStretch()
        
        # Botones
        layout_botones = QHBoxLayout()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialogo.reject)
        
        btn_crear = QPushButton("Crear contraseña")
        btn_crear.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            """
        )
        
        def crear_contrasena():
            # Validar
            if not input_nueva.text():
                label_error.setText("Ingresa una contraseña")
                label_error.setVisible(True)
                return
            
            if len(input_nueva.text()) < 6:
                label_error.setText("Mínimo 6 caracteres")
                label_error.setVisible(True)
                return
            
            if input_nueva.text() != input_repetir.text():
                label_error.setText("Las contraseñas no coinciden")
                label_error.setVisible(True)
                return
            
            # Guardar contraseña
            try:
                establecer_password(usuario_id, input_nueva.text())
                QMessageBox.information(
                    dialogo,
                    "Éxito",
                    "Contraseña creada. Ahora puedes ingresar."
                )
                dialogo.accept()
            except Exception as e:
                label_error.setText(f"Error: {str(e)}")
                label_error.setVisible(True)
        
        btn_crear.clicked.connect(crear_contrasena)
        input_repetir.returnPressed.connect(crear_contrasena)
        
        layout_botones.addStretch()
        layout_botones.addWidget(btn_cancelar)
        layout_botones.addWidget(btn_crear)
        layout.addLayout(layout_botones)
        
        # Mostrar diálogo
        if dialogo.exec():
            # Usuario creó contraseña, intentar login de vuelta
            self.input_contrasena.setText(input_nueva.text())
            self._intentar_login()
