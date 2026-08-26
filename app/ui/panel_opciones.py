"""
Panel de opciones del usuario.

Incluye:
- Información del usuario logueado
- Botón para cambiar contraseña
- Información general (versión, conexión a BD)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

# Importar sesión y diálogo
from app.logica import sesion
from app.ui.dialogo_cambiar_contrasena import DialogoCambiarContrasena


class PanelOpciones(QWidget):
    """
    Panel de opciones e información del usuario.
    
    Estructura:
    - Grupo "Perfil": nombre del usuario
    - Grupo "Seguridad": botón cambiar contraseña
    - Grupo "Información": versión, etc.
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
        titulo = QLabel("Opciones")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(titulo)
        
        # ========================================================================
        # GRUPO: PERFIL
        # ========================================================================
        grupo_perfil = self._crear_grupo_perfil()
        layout.addWidget(grupo_perfil)
        
        # ========================================================================
        # GRUPO: SEGURIDAD
        # ========================================================================
        grupo_seguridad = self._crear_grupo_seguridad()
        layout.addWidget(grupo_seguridad)
        
        # ========================================================================
        # GRUPO: INFORMACIÓN
        # ========================================================================
        grupo_info = self._crear_grupo_informacion()
        layout.addWidget(grupo_info)
        
        # Agregar spacer vertical para que los grupos queden arriba
        layout.addStretch()
    
    def _crear_grupo_perfil(self) -> QGroupBox:
        """
        Crear grupo "Perfil" con información del usuario.
        
        Muestra:
        - Nombre del usuario
        - ID del usuario
        """
        grupo = QGroupBox("Perfil")
        layout = QFormLayout(grupo)
        
        # Obtener datos del usuario actual
        nombre_usuario = sesion.usuario_actual_nombre()
        id_usuario = sesion.usuario_actual_id()
        
        # Nombre
        label_nombre = QLabel(nombre_usuario)
        layout.addRow("Usuario:", label_nombre)
        
        # ID
        label_id = QLabel(str(id_usuario))
        label_id.setStyleSheet("color: #999; font-size: 12px;")
        layout.addRow("ID:", label_id)
        
        return grupo
    
    def _crear_grupo_seguridad(self) -> QGroupBox:
        """
        Crear grupo "Seguridad" con opciones de contraseña.
        
        Incluye:
        - Botón "Cambiar contraseña"
        """
        grupo = QGroupBox("Seguridad")
        layout = QVBoxLayout(grupo)
        layout.setSpacing(12)
        
        # Descripción
        label_desc = QLabel(
            "Cambiar tu contraseña periódicamente es una buena práctica de seguridad."
        )
        label_desc.setStyleSheet("color: #666; font-size: 12px;")
        label_desc.setWordWrap(True)
        layout.addWidget(label_desc)
        
        # Botón cambiar contraseña
        btn_cambiar = QPushButton("Cambiar contraseña")
        btn_cambiar.setMaximumWidth(200)
        btn_cambiar.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            """
        )
        btn_cambiar.clicked.connect(self._mostrar_dialogo_cambiar_contrasena)
        layout.addWidget(btn_cambiar)
        
        # Spacer
        layout.addStretch()
        
        return grupo
    
    def _crear_grupo_informacion(self) -> QGroupBox:
        """
        Crear grupo "Información" con datos de la aplicación.
        
        Muestra:
        - Versión de la app
        - Estado de la conexión a BD
        """
        grupo = QGroupBox("Información")
        layout = QFormLayout(grupo)
        
        # Versión
        label_version = QLabel("1.0.0")
        layout.addRow("Versión:", label_version)
        
        # Estado conexión BD
        # En una app real, esto verificaría la conexión real
        label_conexion = QLabel("Conectado")
        label_conexion.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addRow("Base de datos:", label_conexion)
        
        # Build date (placeholder)
        label_build = QLabel("Agosto 2026")
        layout.addRow("Build:", label_build)
        
        return grupo
    
    def _mostrar_dialogo_cambiar_contrasena(self):
        """
        Mostrar el diálogo modal para cambiar contraseña.
        
        Si el usuario confirma, se actualiza en la BD.
        Si cancela, se desecha.
        """
        dialogo = DialogoCambiarContrasena(self)
        resultado = dialogo.exec()
        
        # Si el usuario aceptó el cambio (resultado == QDialog.Accepted)
        if resultado == 1:  # QDialog.Accepted = 1
            # Aquí podrías hacer algo adicional, como mostrar un mensaje
            pass
