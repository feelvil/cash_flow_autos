"""
ventana_login.py
================
Ventana de login que aparece ANTES de la app principal.

Flujo:
  1. El usuario elige su nombre de un combo (poblado desde la BD).
  2. Escribe su contraseña y presiona Entrar.
  3. Si las credenciales son correctas, la ventana se cierra con éxito y la app
     principal arranca con ese usuario en sesión.

Caso especial "primer ingreso":
  Si el usuario elegido todavía no tiene contraseña (password_hash = NULL), la
  ventana cambia a modo "definir contraseña": pide la clave nueva dos veces y la
  guarda. Después queda logueado.

Cómo la usa main.py:
    login = VentanaLogin()
    if login.exec() == QDialog.Accepted:
        usuario_id = login.usuario_id
        usuario_nombre = login.usuario_nombre
        # ... arrancar la app con ese usuario
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# Lógica de autenticación (con fallback si no está la BD)
try:
    from app.logica.auth import (
        listar_usuarios_activos,
        verificar_login,
        establecer_password,
    )
    BD_DISPONIBLE = True
except ImportError:
    BD_DISPONIBLE = False


class VentanaLogin(QDialog):
    """Ventana modal de login."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Datos del usuario logueado (los lee main.py tras un login exitoso).
        self.usuario_id = None
        self.usuario_nombre = None
        
        self.setWindowTitle("Cash Flow Autos — Ingreso")
        self.setModal(True)
        self.setFixedWidth(420)
        
        self._crear_ui()
        self._cargar_usuarios()
    
    def _crear_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        
        # ═════════════════════════════════════════════════════
        # Encabezado
        # ═════════════════════════════════════════════════════
        lbl_logo = QLabel("📊 Cash Flow Autos")
        font_logo = QFont("Segoe UI", 20)
        font_logo.setWeight(QFont.Weight.Bold)
        lbl_logo.setFont(font_logo)
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("color: #1a1a2e;")
        layout.addWidget(lbl_logo)
        
        lbl_subtitulo = QLabel("Ingresá con tu usuario")
        lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_subtitulo.setStyleSheet("color: #5f6368; font-size: 13px;")
        layout.addWidget(lbl_subtitulo)
        
        layout.addSpacing(8)
        
        # ═════════════════════════════════════════════════════
        # Selección de usuario
        # ═════════════════════════════════════════════════════
        lbl_usuario = QLabel("Usuario:")
        lbl_usuario.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(lbl_usuario)
        
        self.combo_usuario = QComboBox()
        self.combo_usuario.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #d0d7e0;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:focus { border: 2px solid #1a73e8; }
            /* El desplegable (popup): fondo blanco y texto oscuro, para que
               los nombres se vean. Sin esto, hereda texto blanco del tema
               oscuro y queda invisible (blanco sobre blanco). */
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #2c3e50;
                selection-background-color: #e3f2fd;
                selection-color: #1a73e8;
                border: 1px solid #d0d7e0;
                outline: none;
            }
        """)
        self.combo_usuario.currentIndexChanged.connect(self._al_cambiar_usuario)
        layout.addWidget(self.combo_usuario)
        
        # ═════════════════════════════════════════════════════
        # Campo de contraseña (contexto normal)
        # ═════════════════════════════════════════════════════
        self.lbl_password = QLabel("Contraseña:")
        self.lbl_password.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(self.lbl_password)
        
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setPlaceholderText("Ingresá tu contraseña")
        self.input_password.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #2c3e50;
                border: 1px solid #d0d7e0;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #1a73e8; }
        """)
        # Enter en el campo = presionar Entrar.
        self.input_password.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.input_password)
        
        # ═════════════════════════════════════════════════════
        # Campo extra para "primer ingreso" (repetir contraseña)
        # Oculto por defecto; aparece si el usuario no tiene clave.
        # ═════════════════════════════════════════════════════
        self.lbl_password2 = QLabel("Repetir contraseña:")
        self.lbl_password2.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.lbl_password2.setVisible(False)
        layout.addWidget(self.lbl_password2)
        
        self.input_password2 = QLineEdit()
        self.input_password2.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password2.setPlaceholderText("Repetí la contraseña nueva")
        self.input_password2.setStyleSheet(self.input_password.styleSheet())
        self.input_password2.setVisible(False)
        self.input_password2.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.input_password2)
        
        # ═════════════════════════════════════════════════════
        # Mensaje de estado (errores, ayuda del primer ingreso)
        # ═════════════════════════════════════════════════════
        self.lbl_estado = QLabel("")
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setVisible(False)
        layout.addWidget(self.lbl_estado)
        
        layout.addSpacing(8)
        
        # ═════════════════════════════════════════════════════
        # Botón de ingreso
        # ═════════════════════════════════════════════════════
        self.btn_entrar = QPushButton("Entrar")
        self.btn_entrar.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1557c0; }
        """)
        self.btn_entrar.clicked.connect(self._intentar_login)
        layout.addWidget(self.btn_entrar)
    
    def _cargar_usuarios(self):
        """Llena el combo con los usuarios activos de la BD."""
        self.combo_usuario.clear()
        
        if not BD_DISPONIBLE:
            # Modo sin BD: un usuario ficticio para poder ver la pantalla.
            self.combo_usuario.addItem("Sistema (modo prueba)", userData={"id": 1, "tiene_password": True})
            return
        
        try:
            usuarios = listar_usuarios_activos()
            if not usuarios:
                self._mostrar_estado("No hay usuarios activos en la base.", error=True)
                self.btn_entrar.setEnabled(False)
                return
            
            for u in usuarios:
                # Guardamos todo el dict como userData para saber si tiene clave.
                self.combo_usuario.addItem(u["nombre"], userData=u)
                
        except Exception as e:
            self._mostrar_estado(f"No se pudieron cargar los usuarios: {e}", error=True)
            self.btn_entrar.setEnabled(False)
    
    def _al_cambiar_usuario(self):
        """
        Al cambiar de usuario, ajusta la pantalla según tenga o no contraseña.
        """
        datos = self.combo_usuario.currentData()
        if not datos:
            return
        
        # Limpiar campos.
        self.input_password.clear()
        self.input_password2.clear()
        self.lbl_estado.setVisible(False)
        
        if datos.get("tiene_password"):
            # Usuario normal: solo pide contraseña.
            self._modo_primer_ingreso(False)
        else:
            # Primer ingreso: pide definir contraseña (dos veces).
            self._modo_primer_ingreso(True)
    
    def _modo_primer_ingreso(self, activo: bool):
        """Muestra u oculta el segundo campo de contraseña."""
        self.lbl_password2.setVisible(activo)
        self.input_password2.setVisible(activo)
        
        if activo:
            self.lbl_password.setText("Definí tu contraseña:")
            self.input_password.setPlaceholderText("Elegí una contraseña nueva")
            self.btn_entrar.setText("Crear contraseña e ingresar")
            self._mostrar_estado(
                "Es tu primer ingreso: definí una contraseña para tu usuario.",
                error=False
            )
        else:
            self.lbl_password.setText("Contraseña:")
            self.input_password.setPlaceholderText("Ingresá tu contraseña")
            self.btn_entrar.setText("Entrar")
    
    def _intentar_login(self):
        """Valida las credenciales y, si están bien, cierra con éxito."""
        datos = self.combo_usuario.currentData()
        if not datos:
            return
        
        usuario_id = datos["id"]
        password = self.input_password.text()
        
        # Modo sin BD: entrar directo (para desarrollo).
        if not BD_DISPONIBLE:
            self.usuario_id = usuario_id
            self.usuario_nombre = self.combo_usuario.currentText()
            self.accept()
            return
        
        # ─────────────────────────────────────────────
        # Caso primer ingreso: definir contraseña
        # ─────────────────────────────────────────────
        if not datos.get("tiene_password"):
            password2 = self.input_password2.text()
            
            if len(password) < 4:
                self._mostrar_estado("La contraseña debe tener al menos 4 caracteres.", error=True)
                return
            if password != password2:
                self._mostrar_estado("Las contraseñas no coinciden.", error=True)
                return
            
            try:
                establecer_password(usuario_id, password)
            except Exception as e:
                self._mostrar_estado(f"No se pudo guardar la contraseña: {e}", error=True)
                return
            
            # Contraseña creada: queda logueado.
            self.usuario_id = usuario_id
            self.usuario_nombre = datos["nombre"]
            self.accept()
            return
        
        # ─────────────────────────────────────────────
        # Caso normal: verificar contraseña
        # ─────────────────────────────────────────────
        if not password:
            self._mostrar_estado("Ingresá tu contraseña.", error=True)
            return
        
        resultado = verificar_login(usuario_id, password)
        
        if resultado.ok:
            self.usuario_id = resultado.usuario_id
            self.usuario_nombre = resultado.nombre
            self.accept()
        else:
            self._mostrar_estado(resultado.mensaje, error=True)
            self.input_password.clear()
            self.input_password.setFocus()
    
    def _mostrar_estado(self, texto: str, error: bool = False):
        """Muestra un mensaje de estado (rojo si es error, gris si es info)."""
        self.lbl_estado.setText(texto)
        color = "#ea4335" if error else "#5f6368"
        self.lbl_estado.setStyleSheet(f"color: {color}; font-size: 12px;")
        self.lbl_estado.setVisible(True)


# ---------------------------------------------------------------------------
# Prueba visual:  py -m app.ui.ventana_login
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    login = VentanaLogin()
    if login.exec() == QDialog.DialogCode.Accepted:
        print(f"Login OK: usuario_id={login.usuario_id}, nombre={login.usuario_nombre}")
    else:
        print("Login cancelado")
