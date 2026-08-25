# app/logica/reportes.py
"""
Reportes del flujo de fondos.

Este módulo NO calcula el saldo general (eso vive en saldos.py) ni crea/anula
movimientos (eso vive en movimientos.py). Acá armamos las VISTAS de consulta que
va a mostrar la UI y que después alimentan la exportación a Excel:

  1) movimientos_detallados(...)  -> la vista tipo "libro" que reproduce el Excel:
     cada movimiento con toda su clasificación ya resuelta (partida, tipo op.,
     sub-partida, detalle, automotriz, período) y el SALDO ACUMULADO corrido.

  2) resumen_por_clasificacion(session, dimension, ...) -> totales (ingresos,
     egresos, neto, cantidad) agrupados por la dimensión que se pida: partida,
     tipo_operacion, sub_partida, detalle o automotriz. Con wrappers cómodos
     (resumen_por_partida, etc.).

  3) totales_filtrados(...) -> el "pie" del reporte: totales del conjunto filtrado.

Reportes POR PERÍODO: no se reescriben acá. Ya están en saldos.saldo_por_periodo,
así que la UI usa esa. (Duplicar lógica de saldo es justo lo que queremos evitar.)

Todas las funciones son de SOLO LECTURA: no modifican nada, así que se pueden
correr sin miedo contra la base real.
"""

from decimal import Decimal
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database.conexion import SessionLocal
from app.database.models import (
    Movimiento,
    PlanCuenta,
    Partida,
    TipoOperacion,
    SubPartida,
    Detalle,
    Automotriz,
    Periodo,
)
from app.logica.saldos import obtener_saldo_inicial


# ---------------------------------------------------------------------------
# Dimensiones válidas para agrupar en resumen_por_clasificacion.
# Cada una: (Modelo, columna FK en planes_cuentas, es_nullable)
# 'automotriz' es nullable (transversal) -> se resuelve con outerjoin.
# ---------------------------------------------------------------------------
_DIMENSIONES = {
    "partida":        (Partida,       PlanCuenta.partida_id,        False),
    "tipo_operacion": (TipoOperacion, PlanCuenta.tipo_operacion_id, False),
    "sub_partida":    (SubPartida,    PlanCuenta.sub_partida_id,    False),
    "detalle":        (Detalle,       PlanCuenta.detalle_id,        False),
    "automotriz":     (Automotriz,    PlanCuenta.automotriz_id,     True),
}


# ---------------------------------------------------------------------------
# Filtros comunes a todos los reportes.
# Devuelve una LISTA de condiciones para pasar a .where(*condiciones).
# ---------------------------------------------------------------------------
def _condiciones(
    desde: date | None = None,
    hasta: date | None = None,
    automotriz_id: int | None = None,
    periodo_id: int | None = None,
    incluir_anulados: bool = False,
) -> list:
    cond = []
    # Por defecto, los reportes NO cuentan movimientos anulados.
    if not incluir_anulados:
        cond.append(Movimiento.anulado.is_(False))
    if desde is not None:
        cond.append(Movimiento.fecha >= desde)
    if hasta is not None:
        cond.append(Movimiento.fecha <= hasta)
    # El filtro por automotriz mira el plan de cuentas (la automotriz cuelga de ahí).
    if automotriz_id is not None:
        cond.append(PlanCuenta.automotriz_id == automotriz_id)
    if periodo_id is not None:
        cond.append(Movimiento.periodo_id == periodo_id)
    return cond


# ---------------------------------------------------------------------------
# 1) Resumen por clasificación (por categoría / por "cuenta")
# ---------------------------------------------------------------------------
def resumen_por_clasificacion(
    session: Session,
    dimension: str,
    *,
    desde: date | None = None,
    hasta: date | None = None,
    automotriz_id: int | None = None,
    periodo_id: int | None = None,
    incluir_anulados: bool = False,
) -> list[dict]:
    """
    Totaliza ingresos, egresos, neto y cantidad de movimientos, agrupando por la
    'dimension' pedida: 'partida', 'tipo_operacion', 'sub_partida', 'detalle' o
    'automotriz'. Ordena de mayor a menor actividad (ingresos + egresos), así lo
    que más se movió aparece arriba.

    Cada fila del resultado es un dict:
        {nombre, cantidad, ingresos, egresos, neto}
    """
    if dimension not in _DIMENSIONES:
        opciones = ", ".join(_DIMENSIONES)
        raise ValueError(f"Dimensión inválida: {dimension!r}. Opciones válidas: {opciones}.")

    Modelo, fk_col, es_nullable = _DIMENSIONES[dimension]
    cond = _condiciones(desde, hasta, automotriz_id, periodo_id, incluir_anulados)

    consulta = (
        select(
            Modelo.nombre.label("nombre"),
            func.count().label("cantidad"),
            func.coalesce(func.sum(Movimiento.ingresos), 0).label("ingresos"),
            func.coalesce(func.sum(Movimiento.egresos), 0).label("egresos"),
        )
        .select_from(Movimiento)
        .join(PlanCuenta, Movimiento.plan_cuenta_id == PlanCuenta.id)
    )

    # La dimensión se une con join normal, salvo automotriz (nullable -> outerjoin).
    if es_nullable:
        consulta = consulta.outerjoin(Modelo, fk_col == Modelo.id)
    else:
        consulta = consulta.join(Modelo, fk_col == Modelo.id)

    consulta = (
        consulta.where(*cond)
        .group_by(Modelo.nombre)
        # ordenamos por "cuánto se movió" (ingresos + egresos), de mayor a menor
        .order_by((func.sum(Movimiento.ingresos) + func.sum(Movimiento.egresos)).desc())
    )

    resultado = []
    for fila in session.execute(consulta).mappings():
        ingresos = Decimal(fila["ingresos"])
        egresos = Decimal(fila["egresos"])
        resultado.append({
            "nombre": fila["nombre"] if fila["nombre"] is not None else "Transversal (sin automotriz)",
            "cantidad": fila["cantidad"],
            "ingresos": ingresos,
            "egresos": egresos,
            "neto": ingresos - egresos,
        })
    return resultado


# --- Wrappers cómodos para que la UI llame directo ---------------------------
def resumen_por_partida(session: Session, **filtros) -> list[dict]:
    return resumen_por_clasificacion(session, "partida", **filtros)


def resumen_por_tipo_operacion(session: Session, **filtros) -> list[dict]:
    return resumen_por_clasificacion(session, "tipo_operacion", **filtros)


def resumen_por_sub_partida(session: Session, **filtros) -> list[dict]:
    return resumen_por_clasificacion(session, "sub_partida", **filtros)


def resumen_por_detalle(session: Session, **filtros) -> list[dict]:
    return resumen_por_clasificacion(session, "detalle", **filtros)


# ---------------------------------------------------------------------------
# 2) Reporte detallado (vista tipo "libro" que reproduce el Excel)
# ---------------------------------------------------------------------------
def movimientos_detallados(
    session: Session,
    *,
    desde: date | None = None,
    hasta: date | None = None,
    automotriz_id: int | None = None,
    periodo_id: int | None = None,
    incluir_anulados: bool = False,
    incluir_saldo_inicial: bool = True,
) -> list[dict]:
    """
    Lista de movimientos con TODA la clasificación resuelta y un SALDO ACUMULADO
    corrido, ordenados por fecha (y id, para desempatar). Es la vista que más se
    parece a la hoja del Excel, y la que después alimenta la exportación.

    El saldo acumulado se calcula así:
        saldo_acumulado(fila) = saldo_inicial + Σ(ingresos - egresos) hasta esa fila

    La suma corrida la hace PostgreSQL con una "función de ventana" (SUM() OVER),
    que es la forma correcta y eficiente de hacer un acumulado. El saldo_inicial
    (una constante) se lo sumamos en Python.

    OJO con los filtros y el acumulado:
      - Sin filtros de clasificación, el acumulado es el saldo real de caja: la
        última fila tiene que dar el mismo número que saldos.saldo_general.
      - Si filtrás por automotriz (u otra dimensión), el acumulado pasa a ser el
        "flujo acumulado de ese subconjunto", NO un saldo de caja real (porque el
        saldo inicial de hoy es global, no está repartido). Para esos casos podés
        pasar incluir_saldo_inicial=False y arrancar el acumulado desde 0.
    """
    cond = _condiciones(desde, hasta, automotriz_id, periodo_id, incluir_anulados)

    # Función de ventana: suma corrida del flujo, en orden fecha, id.
    flujo_acumulado = func.sum(Movimiento.ingresos - Movimiento.egresos).over(
        order_by=[Movimiento.fecha, Movimiento.id]
    ).label("flujo_acumulado")

    consulta = (
        select(
            Movimiento.id.label("id"),
            Movimiento.fecha.label("fecha"),
            Movimiento.mes.label("mes"),
            PlanCuenta.codigo.label("codigo"),
            Partida.nombre.label("partida"),
            TipoOperacion.nombre.label("tipo_operacion"),
            SubPartida.nombre.label("sub_partida"),
            Detalle.nombre.label("detalle"),
            Periodo.anio.label("periodo_anio"),
            Periodo.mes.label("periodo_mes"),
            Movimiento.comprobante.label("comprobante"),
            Automotriz.nombre.label("automotriz"),
            Movimiento.ingresos.label("ingresos"),
            Movimiento.egresos.label("egresos"),
            Movimiento.neto.label("neto"),
            Movimiento.anulado.label("anulado"),
            flujo_acumulado,
        )
        .select_from(Movimiento)
        .join(PlanCuenta, Movimiento.plan_cuenta_id == PlanCuenta.id)
        .join(Partida, PlanCuenta.partida_id == Partida.id)
        .join(TipoOperacion, PlanCuenta.tipo_operacion_id == TipoOperacion.id)
        .join(SubPartida, PlanCuenta.sub_partida_id == SubPartida.id)
        .join(Detalle, PlanCuenta.detalle_id == Detalle.id)
        # automotriz y período son opcionales -> outerjoin para no perder filas.
        .outerjoin(Automotriz, PlanCuenta.automotriz_id == Automotriz.id)
        .outerjoin(Periodo, Movimiento.periodo_id == Periodo.id)
        .where(*cond)
        .order_by(Movimiento.fecha, Movimiento.id)
    )

    # Base desde la que arranca el acumulado (constante que sumamos en Python).
    base = obtener_saldo_inicial(session) if incluir_saldo_inicial else Decimal("0")

    resultado = []
    for fila in session.execute(consulta).mappings():
        # Período en formato lindo "2026-01" (o None si el movimiento no tiene período).
        if fila["periodo_anio"] is not None:
            periodo_txt = f"{fila['periodo_anio']}-{fila['periodo_mes']:02d}"
        else:
            periodo_txt = None

        resultado.append({
            "id": fila["id"],
            "fecha": fila["fecha"],
            "mes": fila["mes"],
            "codigo": fila["codigo"],
            "partida": fila["partida"],
            "tipo_operacion": fila["tipo_operacion"],
            "sub_partida": fila["sub_partida"],
            "detalle": fila["detalle"],
            "periodo": periodo_txt,
            "comprobante": fila["comprobante"],
            "automotriz": fila["automotriz"] if fila["automotriz"] is not None else "Transversal",
            "ingresos": Decimal(fila["ingresos"]),
            "egresos": Decimal(fila["egresos"]),
            "neto": Decimal(fila["neto"]),
            "anulado": fila["anulado"],
            "saldo_acumulado": base + Decimal(fila["flujo_acumulado"]),
        })
    return resultado


# ---------------------------------------------------------------------------
# 3) Totales del conjunto filtrado (para el "pie" del reporte)
# ---------------------------------------------------------------------------
def totales_filtrados(
    session: Session,
    *,
    desde: date | None = None,
    hasta: date | None = None,
    automotriz_id: int | None = None,
    periodo_id: int | None = None,
    incluir_anulados: bool = False,
) -> dict:
    """
    Totales (cantidad, ingresos, egresos, neto) del conjunto que dan los mismos
    filtros que los otros reportes. Sirve para la fila de totales al pie de una
    grilla o de la exportación.
    """
    cond = _condiciones(desde, hasta, automotriz_id, periodo_id, incluir_anulados)
    consulta = (
        select(
            func.count().label("cantidad"),
            func.coalesce(func.sum(Movimiento.ingresos), 0),
            func.coalesce(func.sum(Movimiento.egresos), 0),
        )
        .select_from(Movimiento)
        .join(PlanCuenta, Movimiento.plan_cuenta_id == PlanCuenta.id)
        .where(*cond)
    )
    cantidad, ingresos, egresos = session.execute(consulta).one()
    ingresos = Decimal(ingresos)
    egresos = Decimal(egresos)
    return {
        "cantidad": cantidad,
        "ingresos": ingresos,
        "egresos": egresos,
        "neto": ingresos - egresos,
    }


# ---------------------------------------------------------------------------
# Prueba rápida (solo lectura, seguro contra la base real)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Correr con:  py -m app.logica.reportes
    with SessionLocal() as session:
        print("=== RESUMEN POR PARTIDA ===")
        for f in resumen_por_partida(session):
            print(f"  {f['nombre']:<14} cant={f['cantidad']:>5}  "
                  f"ing={f['ingresos']:>18,.2f}  egr={f['egresos']:>18,.2f}")

        print("\n=== RESUMEN POR TIPO DE OPERACIÓN ===")
        for f in resumen_por_tipo_operacion(session):
            print(f"  {f['nombre']:<26} neto={f['neto']:>18,.2f}")

        print("\n=== DETALLE (primeras 3 y últimas 3 filas) ===")
        filas = movimientos_detallados(session)
        for f in filas[:3] + filas[-3:]:
            print(f"  {f['fecha']}  {f['partida']:<9} {f['sub_partida']:<18} "
                  f"ing={f['ingresos']:>14,.2f}  egr={f['egresos']:>14,.2f}  "
                  f"acum={f['saldo_acumulado']:>20,.2f}")

        if filas:
            print(f"\nSaldo acumulado final: {filas[-1]['saldo_acumulado']:,.2f}"
                  f"  (tiene que dar 4,613,352,569.94)")
