"""
Pantalla de login: autenticación de usuario.

Características:
- Estilos QSS profesionales (mismo que main_window.py)
- Centrada en la pantalla
- Elementos:
  - Combo con lista de usuarios activos
  - Campo de contraseña
  - Botones Ingresar / Cancelar
  - Validación de credenciales con bcrypt
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QDialog, QSpinBox
)
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QDesktopServices
from PySide6.QtGui import QScreen

# Importar funciones de auth y sesión
from app.logica.auth import listar_usuarios_activos, verificar_login, establecer_password, ResultadoLogin
from app.logica import sesion
from app.ui.main_window import VentanaPrincipal


class VentanaLogin(QWidget):
    """
    Ventana de login principal.
    
    Características:
    - Centrada en la pantalla
    - Estilos QSS cargados desde estilos.qss
    - Flujo de autenticación:
      1. Usuario elige su nombre en el combo
      2. Ingresa contraseña (o define si es primer ingreso)
      3. Clic "Ingresar"
      4. Si OK, abre VentanaPrincipal y cierra login
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Cash Flow Autos — Login")
        self.setGeometry(0, 0, 450, 350)
        
        # Cargar estilos QSS
        self._cargar_estilos()
        
        # Centrar la ventana en la pantalla
        self._centrar_en_pantalla()
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # ========================================================================
        # LOGO / TÍTULO
        # ========================================================================
        titulo = QLabel("Cash Flow Autos")
        titulo.setObjectName("labelTitulo")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        subtitulo = QLabel("Sistema de gestión de flujo de fondos")
        subtitulo.setObjectName("labelSubtitulo")
        subtitulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitulo)
        
        layout.addSpacing(12)
        
        # ========================================================================
        # USUARIO (combo)
        # ========================================================================
        label_usuario = QLabel("Usuario")
        label_usuario.setObjectName("labelTitulo")
        label_usuario.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(label_usuario)
        
        self.combo_usuario = QComboBox()
        
        # Cargar usuarios activos
        usuarios = listar_usuarios_activos()
        if usuarios:
            for u in usuarios:
                self.combo_usuario.addItem(u['nombre'], u['id'])
        else:
            # Si no hay usuarios, agregar placeholder
            self.combo_usuario.addItem("Sin usuarios disponibles", None)
        
        layout.addWidget(self.combo_usuario)
        
        # ========================================================================
        # CONTRASEÑA
        # ========================================================================
        label_contrasena = QLabel("Contraseña")
        label_contrasena.setObjectName("labelTitulo")
        label_contrasena.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(label_contrasena)
        
        self.input_contrasena = QLineEdit()
        self.input_contrasena.setEchoMode(QLineEdit.Password)
        self.input_contrasena.setPlaceholderText("Ingresa tu contraseña")
        self.input_contrasena.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.input_contrasena)
        
        layout.addSpacing(8)
        
        # Mensaje de error
        self.label_error = QLabel("")
        self.label_error.setObjectName("labelError")
        self.label_error.setVisible(False)
        self.label_error.setWordWrap(True)
        layout.addWidget(self.label_error)
        
        layout.addStretch()
        
        # ========================================================================
        # BOTONES
        # ========================================================================
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(12)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("botonSecundario")
        btn_cancelar.clicked.connect(self.close)
        btn_cancelar.setMinimumHeight(36)
        
        btn_ingresar = QPushButton("Ingresar")
        btn_ingresar.setObjectName("botonExito")  # Verde
        btn_ingresar.clicked.connect(self._intentar_login)
        btn_ingresar.setMinimumHeight(36)
        
        layout_botones.addWidget(btn_cancelar)
        layout_botones.addWidget(btn_ingresar)
        layout.addLayout(layout_botones)
    
    def _cargar_estilos(self):
        """
        Cargar archivo estilos.qss y aplicarlo a la ventana.
        
        Busca estilos.qss en:
        1. Raíz del proyecto
        2. app/ui/
        """
        # Rutas posibles
        rutas = [
            Path(__file__).parent.parent.parent / "estilos.qss",  # raíz/estilos.qss
            Path(__file__).parent / "estilos.qss",                # app/ui/estilos.qss
        ]
        
        # Buscar y cargar
        for ruta in rutas:
            if ruta.exists():
                try:
                    with open(ruta, 'r', encoding='utf-8') as f:
                        estilos = f.read()
                    self.setStyleSheet(estilos)
                    print(f"✓ Estilos de login cargados desde: {ruta}")
                    return
                except Exception as e:
                    print(f"✗ Error cargando estilos desde {ruta}: {e}")
        
        print("⚠ No se encontró estilos.qss para login, usando estilos por defecto")
    
    def _centrar_en_pantalla(self):
        """
        Centrar la ventana en el centro de la pantalla.
        
        Calcula la posición basada en el tamaño de la pantalla.
        """
        # Obtener información de la pantalla
        screen = self.screen()
        if screen:
            # Geometría de la pantalla
            screen_geometry = screen.availableGeometry()
            
            # Calcular posición para centrar
            x = (screen_geometry.width() - self.width()) // 2
            y = (screen_geometry.height() - self.height()) // 2
            
            # Asegurarse de que la ventana no se salga de la pantalla
            x = max(0, x)
            y = max(0, y)
            
            # Establecer posición
            self.move(x, y)
    
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
            self.label_error.setText("Selecciona un usuario válido")
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
            self._dialogo_primera_contrasena(usuario_id, usuario_nombre)
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
    
    def _dialogo_primera_contrasena(self, usuario_id: int, usuario_nombre: str):
        """
        Diálogo para usuario sin contraseña (primer ingreso).
        
        Le pide que ingrese su contraseña por primera vez.
        """
        # Crear diálogo
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Primera contraseña")
        dialogo.setGeometry(0, 0, 400, 250)
        dialogo.setModal(True)
        
        # Cargar estilos en el diálogo también
        self._cargar_estilos_dialogo(dialogo)
        
        # Centrar diálogo
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - dialogo.width()) // 2
        y = (screen_geometry.height() - dialogo.height()) // 2
        dialogo.move(max(0, x), max(0, y))
        
        layout = QVBoxLayout(dialogo)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Mensaje de bienvenida
        label_bienvenida = QLabel(f"¡Hola {usuario_nombre}!")
        label_bienvenida.setObjectName("labelTitulo")
        layout.addWidget(label_bienvenida)
        
        label_instruccion = QLabel("Ingresa una contraseña para tu cuenta:")
        label_instruccion.setObjectName("labelSubtitulo")
        layout.addWidget(label_instruccion)
        
        # Contraseña nueva
        label_nueva = QLabel("Contraseña")
        label_nueva.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(label_nueva)
        
        input_nueva = QLineEdit()
        input_nueva.setEchoMode(QLineEdit.Password)
        input_nueva.setPlaceholderText("Mínimo 6 caracteres")
        layout.addWidget(input_nueva)
        
        # Repetir contraseña
        label_repetir = QLabel("Repetir contraseña")
        label_repetir.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(label_repetir)
        
        input_repetir = QLineEdit()
        input_repetir.setEchoMode(QLineEdit.Password)
        input_repetir.setPlaceholderText("Repite la contraseña")
        layout.addWidget(input_repetir)
        
        # Mensaje de error
        label_error = QLabel("")
        label_error.setObjectName("labelError")
        label_error.setVisible(False)
        label_error.setWordWrap(True)
        layout.addWidget(label_error)
        
        layout.addStretch()
        
        # Botones
        layout_botones = QHBoxLayout()
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("botonSecundario")
        btn_cancelar.clicked.connect(dialogo.reject)
        btn_cancelar.setMinimumHeight(36)
        
        btn_crear = QPushButton("Crear contraseña")
        btn_crear.setObjectName("botonExito")
        btn_crear.setMinimumHeight(36)
        
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
    
    def _cargar_estilos_dialogo(self, dialogo):
        """
        Cargar estilos para un diálogo (helper).
        """
        rutas = [
            Path(__file__).parent.parent.parent / "estilos.qss",
            Path(__file__).parent / "estilos.qss",
        ]
        
        for ruta in rutas:
            if ruta.exists():
                try:
                    with open(ruta, 'r', encoding='utf-8') as f:
                        estilos = f.read()
                    dialogo.setStyleSheet(estilos)
                    return
                except:
                    pass
