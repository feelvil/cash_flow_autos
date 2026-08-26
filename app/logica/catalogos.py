"""
catalogos.py
============
Funciones de SOLO LECTURA para llenar los combos de la interfaz con datos
reales de la base (en vez de códigos ficticios escritos a mano).

La idea es simple: la pantalla de Cobros necesita mostrar los códigos de
INGRESOS, la de Pagos los de EGRESOS, y al elegir un código queremos poder
mostrar toda su clasificación (Partida, Sub-Partida, Detalle, Automotriz).
Todo eso ya está en la tabla `planes_cuentas`, enlazado por relaciones, así
que sólo hay que leerlo y darle un formato lindo para el combo.

Nada de esto ESCRIBE en la base: son consultas nada más.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database.conexion import SessionLocal
from app.database.models import PlanCuenta, Partida


# ---------------------------------------------------------------------------
# Estructura de datos que devolvemos por cada código.
# ---------------------------------------------------------------------------
# Usamos un dataclass (en vez de un dict suelto) para que quede claro qué campos
# hay y para que el editor autocomplete. Cada CodigoCuenta representa una fila
# del plan de cuentas ya "resuelta" (con los nombres de la jerarquía, no los ids).
@dataclass
class CodigoCuenta:
    codigo: int                 # ej: 1041131
    partida: str                # ej: "INGRESOS"
    tipo_operacion: str         # ej: "Transferencia"
    sub_partida: str            # ej: "Rentas"
    detalle: str                # ej: "NEUQUÉN 1° Q"
    automotriz: str | None      # ej: "1 - VW - Volkswagen" o None si es transversal

    def etiqueta(self) -> str:
        """
        Texto que se muestra en el combo. Formato:
            "1041131 — Rentas · NEUQUÉN 1° Q"
        Elegimos mostrar sub-partida y detalle porque es lo que identifica el
        movimiento a ojo; la partida (INGRESOS/EGRESOS) ya está implícita porque
        el combo de Cobros sólo trae ingresos y el de Pagos sólo egresos.
        """
        base = f"{self.codigo} — {self.sub_partida} · {self.detalle}"
        if self.automotriz:
            # El nombre de automotriz suele venir como "1 - VW - Volkswagen";
            # agregamos sólo la sigla corta para no hacer la etiqueta larguísima.
            base += f"  [{self.automotriz}]"
        return base


# ---------------------------------------------------------------------------
# Función interna: arma la consulta base con todas las relaciones ya cargadas.
# ---------------------------------------------------------------------------
def _query_planes(sesion, tipo_partida: str | None):
    """
    Devuelve una lista de PlanCuenta (activos), opcionalmente filtrados por el
    'tipo' de la partida ('cobro' o 'pago').

    Usamos joinedload para traer en UNA sola consulta el plan + su partida +
    tipo_op + sub_partida + detalle + automotriz. Sin esto, SQLAlchemy haría
    una consulta extra por cada relación de cada fila (el clásico problema
    "N+1 queries"), y con ~250 códigos se notaría la lentitud.
    """
    consulta = (
        select(PlanCuenta)
        .options(
            joinedload(PlanCuenta.partida),
            joinedload(PlanCuenta.tipo_operacion),
            joinedload(PlanCuenta.sub_partida),
            joinedload(PlanCuenta.detalle),
            joinedload(PlanCuenta.automotriz),
        )
        .where(PlanCuenta.activo == True)  # noqa: E712  (SQLAlchemy necesita ==)
    )

    # Si nos pidieron sólo cobros o sólo pagos, filtramos por el tipo de la partida.
    if tipo_partida is not None:
        consulta = consulta.join(PlanCuenta.partida).where(Partida.tipo == tipo_partida)

    return sesion.execute(consulta).scalars().all()


# ---------------------------------------------------------------------------
# Función interna: convierte un PlanCuenta (ORM) en un CodigoCuenta (plano).
# ---------------------------------------------------------------------------
def _a_codigo_cuenta(pc: PlanCuenta) -> CodigoCuenta:
    return CodigoCuenta(
        codigo=pc.codigo,
        partida=pc.partida.nombre,
        tipo_operacion=pc.tipo_operacion.nombre,
        sub_partida=pc.sub_partida.nombre,
        detalle=pc.detalle.nombre,
        automotriz=pc.automotriz.nombre if pc.automotriz else None,
    )


# ---------------------------------------------------------------------------
# API pública que usa la UI.
# ---------------------------------------------------------------------------
def obtener_codigos(tipo: str | None = None) -> list[CodigoCuenta]:
    """
    Devuelve la lista de códigos de cuenta, ordenados por número de código.

    Args:
        tipo: 'cobro' para la pantalla de Cobros (trae partidas INGRESOS),
              'pago' para la pantalla de Pagos (trae partidas EGRESOS),
              None para traer todos (útil en Reportes o para un buscador global).

    Retorna:
        Lista de CodigoCuenta ya resueltos. Si hay un problema de conexión,
        propaga la excepción para que la UI decida (ej: caer a datos de prueba).
    """
    with SessionLocal() as sesion:
        planes = _query_planes(sesion, tipo)
        codigos = [_a_codigo_cuenta(pc) for pc in planes]

    # Ordenamos por código (numérico) para que el combo salga prolijo.
    codigos.sort(key=lambda c: c.codigo)
    return codigos


def obtener_codigos_cobro() -> list[CodigoCuenta]:
    """Atajo para la pantalla de Cobros: sólo códigos de INGRESOS."""
    return obtener_codigos(tipo="cobro")


def obtener_codigos_pago() -> list[CodigoCuenta]:
    """Atajo para la pantalla de Pagos: sólo códigos de EGRESOS."""
    return obtener_codigos(tipo="pago")


def buscar_por_codigo(codigo: int) -> CodigoCuenta | None:
    """
    Busca un código puntual y devuelve su clasificación completa, o None si no
    existe. Sirve para que, cuando el usuario elige/escribe un código en el
    combo, la pantalla pueda mostrar en vivo la Partida / Sub-Partida / Detalle.
    """
    with SessionLocal() as sesion:
        consulta = (
            select(PlanCuenta)
            .options(
                joinedload(PlanCuenta.partida),
                joinedload(PlanCuenta.tipo_operacion),
                joinedload(PlanCuenta.sub_partida),
                joinedload(PlanCuenta.detalle),
                joinedload(PlanCuenta.automotriz),
            )
            .where(PlanCuenta.codigo == codigo)
        )
        pc = sesion.execute(consulta).scalars().first()
        return _a_codigo_cuenta(pc) if pc else None


# ---------------------------------------------------------------------------
# Prueba rápida desde consola:  py -m app.logica.catalogos
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("== Códigos de COBRO (primeros 5) ==")
    for c in obtener_codigos_cobro()[:5]:
        print("  ", c.etiqueta())

    print("\n== Códigos de PAGO (primeros 5) ==")
    for c in obtener_codigos_pago()[:5]:
        print("  ", c.etiqueta())

    print("\n== Buscar código 1041131 ==")
    encontrado = buscar_por_codigo(1041131)
    print("  ", encontrado.etiqueta() if encontrado else "(no existe)")
