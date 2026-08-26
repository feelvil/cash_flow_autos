"""
Modelos SQLAlchemy: definición de todas las tablas de la BD.

Tablas:
- usuarios: quiénes pueden usar la app
- partidas: INGRESOS, EGRESOS, etc.
- tipos_operacion: Transferencia, BtoB, etc.
- sub_partidas: Rentas, Registración, etc.
- detalles: NEUQUÉN, CORRIENTES, etc.
- automotrices: VW, Plan Rombo, etc.
- periodos: períodos contables (mes/año)
- planes_cuentas: mapeo código → jerarquía completa
- movimientos: tabla central de cobros/pagos
"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base para todos los modelos."""
    pass


# ============================================================================
# TABLAS DE DIMENSIONES (catálogos)
# ============================================================================

class Usuario(Base):
    """
    Usuarios del sistema.
    
    Campos:
    - id: Identificador único
    - nombre: Nombre del usuario
    - activo: Si puede usar la app
    - password_hash: Contraseña hasheada con bcrypt (nullable para primer ingreso)
    - creado_en: Timestamp de creación
    """
    __tablename__ = "usuarios"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    movimientos = relationship("Movimiento", back_populates="usuario")


class Partida(Base):
    """
    Primer nivel de clasificación: INGRESOS, EGRESOS, SALDO INICIAL.
    
    Campos:
    - id: Identificador único
    - nombre: Ej: "INGRESOS", "EGRESOS"
    - tipo: "cobro", "pago", "saldo_inicial"
    - activa: Si está en uso
    - creado_en: Timestamp
    """
    __tablename__ = "partidas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    activa: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    sub_partidas = relationship("SubPartida", back_populates="partida")
    planes_cuentas = relationship("PlanCuentas", back_populates="partida")


class TiposOperacion(Base):
    """
    Segundo nivel: cómo se cobra/paga.
    
    Ej: Transferencia, BtoB, Cheque, Efectivo.
    """
    __tablename__ = "tipos_operacion"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    sub_partidas = relationship("SubPartida", back_populates="tipo_operacion")
    planes_cuentas = relationship("PlanCuentas", back_populates="tipo_operacion")


class SubPartida(Base):
    """
    Tercer nivel: categorías específicas.
    
    Ej: Rentas, Registración, Entidades co-participadas, Sueldos.
    """
    __tablename__ = "sub_partidas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id"), nullable=False)
    tipo_operacion_id: Mapped[int] = mapped_column(ForeignKey("tipos_operacion.id"), nullable=False)
    activa: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    partida = relationship("Partida", back_populates="sub_partidas")
    tipo_operacion = relationship("TiposOperacion", back_populates="sub_partidas")
    detalles = relationship("Detalle", back_populates="sub_partida")
    planes_cuentas = relationship("PlanCuentas", back_populates="sub_partida")


class Detalle(Base):
    """
    Cuarto nivel: descripción específica.
    
    Ej: NEUQUÉN 1° Q, CORRIENTES 1° Q, MISIONES.
    """
    __tablename__ = "detalles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    sub_partida_id: Mapped[int] = mapped_column(ForeignKey("sub_partidas.id"), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    sub_partida = relationship("SubPartida", back_populates="detalles")
    planes_cuentas = relationship("PlanCuentas", back_populates="detalle")


class Automotriz(Base):
    """
    Dimensión transversal: grupos automotrices.
    
    Ej: VW, Plan Rombo, Chevrolet, Fiat, Yamaha.
    """
    __tablename__ = "automotrices"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    planes_cuentas = relationship("PlanCuentas", back_populates="automotriz")


class Periodo(Base):
    """
    Período contable (mes/año).
    
    Campos:
    - fecha_inicio, fecha_fin: Rango del período
    - mes, año: Para búsquedas rápidas
    - descripcion: Ej: "Enero 2026", "2026-01"
    """
    __tablename__ = "periodos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    año: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    movimientos = relationship("Movimiento", back_populates="periodo")


# ============================================================================
# TABLA HUB: PLANES DE CUENTAS
# ============================================================================

class PlanCuentas(Base):
    """
    Mapeo de códigos a la jerarquía completa.
    
    Cada código mapea a: Partida → Tipo Op. → Sub-Partida → Detalle → Automotriz (opcional).
    """
    __tablename__ = "planes_cuentas"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[int] = mapped_column(unique=True, nullable=False)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id"), nullable=False)
    tipo_operacion_id: Mapped[int] = mapped_column(ForeignKey("tipos_operacion.id"), nullable=False)
    sub_partida_id: Mapped[int] = mapped_column(ForeignKey("sub_partidas.id"), nullable=False)
    detalle_id: Mapped[int] = mapped_column(ForeignKey("detalles.id"), nullable=False)
    automotriz_id: Mapped[Optional[int]] = mapped_column(ForeignKey("automotrices.id"), nullable=True)
    derechos: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    partida = relationship("Partida", back_populates="planes_cuentas")
    tipo_operacion = relationship("TiposOperacion", back_populates="planes_cuentas")
    sub_partida = relationship("SubPartida", back_populates="planes_cuentas")
    detalle = relationship("Detalle", back_populates="planes_cuentas")
    automotriz = relationship("Automotriz", back_populates="planes_cuentas")
    movimientos = relationship("Movimiento", back_populates="plan_cuenta")


# ============================================================================
# TABLA CENTRAL: MOVIMIENTOS
# ============================================================================

class Movimiento(Base):
    """
    Tabla central: cada cobro o pago.
    
    Campos principales:
    - fecha: Cuándo ocurrió
    - plan_cuenta_id: Toda la clasificación
    - ingresos / egresos: Montos (nunca negativo)
    - neto: ingresos - egresos (puede ser negativo)
    - usuario_id: Quién lo cargó
    - anulado: Si se anuló (nunca se borra)
    - movimiento_anulacion_id: Referencia a la reversa si fue anulado
    """
    __tablename__ = "movimientos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)  # Derivado de fecha
    plan_cuenta_id: Mapped[int] = mapped_column(ForeignKey("planes_cuentas.id"), nullable=False)
    periodo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("periodos.id"), nullable=True)
    comprobante: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ingresos: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    egresos: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    neto: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    anulado: Mapped[bool] = mapped_column(default=False)
    movimiento_anulacion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("movimientos.id"), nullable=True
    )
    descripcion_adicional: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    plan_cuenta = relationship("PlanCuentas", back_populates="movimientos")
    periodo = relationship("Periodo", back_populates="movimientos")
    usuario = relationship("Usuario", back_populates="movimientos")
    # Auto-referencia: movimiento que lo anula
    movimiento_que_lo_anula = relationship(
        "Movimiento",
        remote_side=[id],
        foreign_keys=[movimiento_anulacion_id],
        backref="movimiento_anulado_por"
    )


# ============================================================================
# TABLA DE AUDITORÍA (preparada para v2)
# ============================================================================

class LogAuditoria(Base):
    """
    Registro de cambios (implementación completa en v2).
    
    Por ahora solo estructura, sin lógica de llenado automático.
    """
    __tablename__ = "logs_auditoria"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tabla_afectada: Mapped[str] = mapped_column(String, nullable=False)
    registro_id: Mapped[int] = mapped_column(Integer, nullable=False)
    operacion: Mapped[str] = mapped_column(String, nullable=False)  # INSERT, UPDATE, DELETE
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    datos_anteriores: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # JSON
    datos_nuevos: Mapped[str] = mapped_column(String, nullable=False)  # JSON
    ejecutado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    usuario = relationship("Usuario")
