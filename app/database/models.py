"""
models.py
=========
Modelos de SQLAlchemy que representan las tablas de la base de datos.

Idea clave:
  - Cada CLASE de Python  = una TABLA en PostgreSQL.
  - Cada ATRIBUTO de la clase = una COLUMNA de esa tabla.

Usamos el estilo "2.0" de SQLAlchemy (Mapped / mapped_column). Es el recomendado
hoy: las columnas se declaran con anotaciones de tipo de Python, lo que hace el
código más legible y permite que el editor (Pylance) nos avise de errores.

IMPORTANTE: este archivo NO crea las tablas en la base por sí solo. Solo las
DESCRIBE. Quien las crea de verdad es Alembic, que lee estos modelos para
generar la migración (ver el paso de Alembic en las instrucciones).
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Date,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base declarativa
# ---------------------------------------------------------------------------
# Todas nuestras tablas heredan de esta clase Base. SQLAlchemy usa "Base.metadata"
# como un catálogo de todas las tablas; Alembic lee esa metadata para generar
# y comparar migraciones automáticamente.
class Base(DeclarativeBase):
    pass


# ===========================================================================
# 1. USUARIOS  -> quiénes pueden usar el sistema (sin roles granulares en v1)
# ===========================================================================
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    # activo: si un usuario deja la empresa, lo marcamos inactivo en vez de borrarlo,
    # así los movimientos que cargó siguen apuntando a un usuario válido.
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relación inversa: desde un usuario podemos llegar a todos sus movimientos.
    movimientos: Mapped[list["Movimiento"]] = relationship(back_populates="usuario")


# ===========================================================================
# 2. PARTIDAS  -> primer nivel de clasificación (INGRESOS, EGRESOS, SALDO INICIAL)
# ===========================================================================
class Partida(Base):
    __tablename__ = "partidas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # nombre único: no puede haber dos partidas "INGRESOS", por ejemplo.
    nombre: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    # tipo: "cobro", "pago" o "saldo_inicial" (caso especial).
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    activa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ===========================================================================
# 3. TIPOS_OPERACION  -> cómo se cobra/paga (Transferencia, BtoB, Cheque, ...)
# ===========================================================================
class TipoOperacion(Base):
    __tablename__ = "tipos_operacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ===========================================================================
# 4. SUB_PARTIDAS  -> tercer nivel (Rentas, Registración, Sueldos, ...)
#    Una sub-partida pertenece a una Partida y a un Tipo de Operación.
# ===========================================================================
class SubPartida(Base):
    __tablename__ = "sub_partidas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    # Claves foráneas: enlazan esta fila con su partida y su tipo de operación.
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id"), nullable=False)
    tipo_operacion_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_operacion.id"), nullable=False
    )
    activa: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # La combinación (nombre + partida + tipo_operacion) no se puede repetir.
    __table_args__ = (
        UniqueConstraint(
            "nombre",
            "partida_id",
            "tipo_operacion_id",
            name="uq_sub_partidas_nombre_partida_tipo",
        ),
    )

    # Relaciones: nos dejan navegar el objeto sin escribir JOINs a mano.
    partida: Mapped["Partida"] = relationship()
    tipo_operacion: Mapped["TipoOperacion"] = relationship()
    detalles: Mapped[list["Detalle"]] = relationship(back_populates="sub_partida")


# ===========================================================================
# 5. DETALLES  -> cuarto nivel (NEUQUÉN 1° Q, CORRIENTES 1° Q, AMN, ...)
#    Cada detalle cuelga de una sub-partida.
# ===========================================================================
class Detalle(Base):
    __tablename__ = "detalles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False)
    sub_partida_id: Mapped[int] = mapped_column(
        ForeignKey("sub_partidas.id"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "nombre", "sub_partida_id", name="uq_detalles_nombre_sub_partida"
        ),
    )

    sub_partida: Mapped["SubPartida"] = relationship(back_populates="detalles")


# ===========================================================================
# 6. AUTOMOTRICES  -> dimensión transversal (1-VW, 2-PR, 3-GM, ...)
# ===========================================================================
class Automotriz(Base):
    __tablename__ = "automotrices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # codigo lo guardamos como texto porque en el Excel es "1", "2", etc.
    # (podría empezar con cero o tener letras a futuro; el texto es más flexible).
    codigo: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ===========================================================================
# 7. PERIODOS  -> período contable de referencia del movimiento
#    (no es lo mismo la FECHA de cobro que el PERÍODO al que corresponde).
# ===========================================================================
class Periodo(Base):
    __tablename__ = "periodos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    mes: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 a 12
    # OJO: en el modelo escrito la columna se llama "año", pero usar la "ñ" en
    # nombres de columnas/atributos trae problemas de codificación en Windows y
    # con algunas herramientas. Por eso la llamamos "anio" en la base y en el código.
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String, nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        # No puede haber dos períodos para el mismo mes/año.
        UniqueConstraint("mes", "anio", name="uq_periodos_mes_anio"),
        # Índice para buscar rápido por rango de fechas.
        Index("idx_periodos_fechas", "fecha_inicio", "fecha_fin"),
    )

    movimientos: Mapped[list["Movimiento"]] = relationship(back_populates="periodo")


# ===========================================================================
# 8. PLANES_CUENTAS  -> el "hub": mapea un CÓDIGO a toda la jerarquía
#    (Partida -> Tipo Op. -> Sub-Partida -> Detalle -> Automotriz).
# ===========================================================================
class PlanCuenta(Base):
    __tablename__ = "planes_cuentas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # codigo: el identificador del Excel, ej: 1041131. Único e indexado.
    codigo: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id"), nullable=False)
    tipo_operacion_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_operacion.id"), nullable=False
    )
    sub_partida_id: Mapped[int] = mapped_column(
        ForeignKey("sub_partidas.id"), nullable=False
    )
    detalle_id: Mapped[int] = mapped_column(ForeignKey("detalles.id"), nullable=False)
    # automotriz es OPCIONAL (nullable): si es NULL, el plan es transversal.
    automotriz_id: Mapped[int | None] = mapped_column(
        ForeignKey("automotrices.id"), nullable=True
    )
    derechos: Mapped[str | None] = mapped_column(String, nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relaciones hacia cada dimensión de la jerarquía.
    partida: Mapped["Partida"] = relationship()
    tipo_operacion: Mapped["TipoOperacion"] = relationship()
    sub_partida: Mapped["SubPartida"] = relationship()
    detalle: Mapped["Detalle"] = relationship()
    automotriz: Mapped["Automotriz | None"] = relationship()
    movimientos: Mapped[list["Movimiento"]] = relationship(back_populates="plan_cuenta")


# ===========================================================================
# 9. MOVIMIENTOS  -> la tabla central: cada cobro o pago registrado.
# ===========================================================================
class Movimiento(Base):
    __tablename__ = "movimientos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)  # fecha del movimiento
    mes: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12, derivado de fecha

    # Toda la clasificación viaja a través del plan de cuentas.
    plan_cuenta_id: Mapped[int] = mapped_column(
        ForeignKey("planes_cuentas.id"), nullable=False
    )
    # El período es opcional (ej: rentas de diciembre cobradas en enero).
    periodo_id: Mapped[int | None] = mapped_column(
        ForeignKey("periodos.id"), nullable=True
    )

    comprobante: Mapped[str | None] = mapped_column(String, nullable=True)

    # Montos: siempre >= 0. El "signo" lo determina si es ingreso o egreso.
    ingresos: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0, server_default=text("0")
    )
    egresos: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0, server_default=text("0")
    )
    # neto = ingresos - egresos. Lo guardamos calculado para simplificar reportes.
    neto: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=0, server_default=text("0")
    )

    # NOTA: NO guardamos "saldo_acumulado" como columna. El saldo corrido se
    # calcula en la consulta (con SUM() OVER ...), así siempre está consistente
    # y no queda "viejo" si se anula un movimiento anterior.

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Anulación: nunca borramos. Marcamos anulado=true y enlazamos al asiento
    # de reversa que lo corrige.
    anulado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    movimiento_anulacion_id: Mapped[int | None] = mapped_column(
        ForeignKey("movimientos.id"), nullable=True
    )
    descripcion_adicional: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        # Índices pensados para los reportes más comunes.
        Index("idx_movimientos_fecha_anulado", "fecha", "anulado"),
        Index("idx_movimientos_plan_cuenta_anulado", "plan_cuenta_id", "anulado"),
        Index("idx_movimientos_usuario_creado", "usuario_id", "creado_en"),
    )

    # Relaciones.
    plan_cuenta: Mapped["PlanCuenta"] = relationship(back_populates="movimientos")
    periodo: Mapped["Periodo | None"] = relationship(back_populates="movimientos")
    usuario: Mapped["Usuario"] = relationship(back_populates="movimientos")
    # Auto-referencia: el movimiento de reversa que anula a este (si aplica).
    anulacion: Mapped["Movimiento | None"] = relationship(remote_side=[id])


# ===========================================================================
# 10. SALDOS_INICIALES  -> el saldo de arranque del flujo (punto de partida).
#     NO es un movimiento ni un plan de cuentas: es el número desde el cual
#     empieza a calcularse todo el saldo. Hoy hay una sola fila (global), pero
#     la tabla queda preparada para: (a) saldo inicial por automotriz, y
#     (b) un saldo inicial nuevo por cada ejercicio (ej: al arrancar 2027).
# ===========================================================================
class SaldoInicial(Base):
    __tablename__ = "saldos_iniciales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Fecha desde la que aplica este saldo inicial (ej: 2026-01-01).
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    # El monto de arranque. Es plata, por eso Numeric (nunca float).
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    # Opcional: si algún día el saldo inicial se abre por automotriz.
    # NULL = saldo inicial GLOBAL (el caso actual).
    automotriz_id: Mapped[int | None] = mapped_column(
        ForeignKey("automotrices.id"), nullable=True
    )
    descripcion: Mapped[str | None] = mapped_column(String, nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        # Evita cargar dos saldos iniciales para la misma fecha + automotriz.
        # (Ojo: en Postgres, si automotriz_id es NULL, esta regla no lo frena;
        #  por eso el script de carga igual chequea antes de insertar.)
        UniqueConstraint(
            "fecha", "automotriz_id", name="uq_saldos_iniciales_fecha_automotriz"
        ),
    )

    automotriz: Mapped["Automotriz | None"] = relationship()
