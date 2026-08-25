# app/logica/saldos.py
"""
Cálculo de saldos del flujo de fondos.

Este es el primer módulo de la capa de lógica: acá la app "usa" todo lo que
migramos del Excel. La regla base es una sola y se repite en todas las funciones:

    saldo = saldo_inicial + Σ(ingresos − egresos)

...donde la suma es SOLO sobre movimientos NO anulados. Los movimientos anulados
quedan en la base (nunca se borran), pero no se cuentan para el saldo.

Nada de esto guarda un "saldo" en ninguna columna: siempre se calcula desde los
movimientos, así nunca queda un número viejo o escrito a mano (que fue justo el
problema que encontramos en el Excel).
"""

from decimal import Decimal
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database.conexion import SessionLocal
from app.database.models import (
    Movimiento,
    PlanCuenta,
    Automotriz,
    Periodo,
    SaldoInicial,
)


# ---------------------------------------------------------------------------
# Helpers internos (los que hacen el trabajo pesado)
# ---------------------------------------------------------------------------

def obtener_saldo_inicial(session: Session) -> Decimal:
    """
    Devuelve el saldo inicial (el punto de arranque al 2026-01-01).

    Hoy hay una sola fila global en `saldos_iniciales`, pero sumamos TODAS por
    si en el futuro se carga un saldo inicial por automotriz o por ejercicio.
    Así este código no se rompe cuando eso cambie.

    Sumamos solo los saldos iniciales con activo=True.

    OJO con el futuro: sumar todas las filas es correcto MIENTRAS el saldo
    inicial sea uno solo (global) o se abra por automotriz sobre el mismo punto
    de arranque (ej: 2026-01-01). El día que se cargue un saldo inicial nuevo
    por ejercicio (ej: 2027-01-01), NO va a haber que sumarlos: habrá que elegir
    el que corresponda por fecha, porque si no se duplica. Lo dejamos anotado
    para esa etapa.
    """
    total = session.scalar(
        select(func.coalesce(func.sum(SaldoInicial.monto), 0))
        .where(SaldoInicial.activo.is_(True))
    )
    # func.coalesce(..., 0) evita que devuelva None si la tabla estuviera vacía.
    return Decimal(total)


def _suma_neto(session: Session, hasta_fecha: date | None = None) -> Decimal:
    """
    Σ(ingresos − egresos) sobre movimientos NO anulados.

    Si se pasa `hasta_fecha`, solo cuenta movimientos con fecha <= esa fecha
    (sirve para preguntar "¿cuál era el saldo al día X?").

    El guion bajo del nombre (_suma_neto) es una convención de Python: avisa
    que es una función "de uso interno" del módulo, no pensada para llamar
    desde afuera.
    """
    condiciones = [Movimiento.anulado.is_(False)]
    if hasta_fecha is not None:
        condiciones.append(Movimiento.fecha <= hasta_fecha)

    consulta = (
        select(func.coalesce(func.sum(Movimiento.ingresos - Movimiento.egresos), 0))
        .where(*condiciones)
    )
    return Decimal(session.scalar(consulta))


# ---------------------------------------------------------------------------
# Saldo general
# ---------------------------------------------------------------------------

def saldo_general(session: Session, hasta_fecha: date | None = None) -> Decimal:
    """
    Saldo general de todo el flujo: saldo_inicial + Σ(ingresos − egresos).

    Es el número "grande" que va arriba de todo en la pantalla principal.
    """
    return obtener_saldo_inicial(session) + _suma_neto(session, hasta_fecha)


def totales_generales(session: Session, hasta_fecha: date | None = None) -> dict:
    """
    Desglose completo del saldo general en un solo lugar, listo para mostrar
    en pantalla o en un reporte. Devuelve un diccionario con:

        saldo_inicial, ingresos, egresos, neto, saldo_final

    Se calcula todo con UNA sola consulta a la base (ingresos y egresos juntos)
    más la lectura del saldo inicial, así no golpeamos la base de más.
    """
    condiciones = [Movimiento.anulado.is_(False)]
    if hasta_fecha is not None:
        condiciones.append(Movimiento.fecha <= hasta_fecha)

    consulta = (
        select(
            func.coalesce(func.sum(Movimiento.ingresos), 0),
            func.coalesce(func.sum(Movimiento.egresos), 0),
        )
        .where(*condiciones)
    )
    ingresos, egresos = session.execute(consulta).one()
    ingresos = Decimal(ingresos)
    egresos = Decimal(egresos)
    saldo_inicial = obtener_saldo_inicial(session)

    return {
        "saldo_inicial": saldo_inicial,
        "ingresos": ingresos,
        "egresos": egresos,
        "neto": ingresos - egresos,
        "saldo_final": saldo_inicial + ingresos - egresos,
    }


# ---------------------------------------------------------------------------
# Saldo por automotriz
# ---------------------------------------------------------------------------

def saldo_por_automotriz(session: Session, hasta_fecha: date | None = None) -> list[dict]:
    """
    Neto (ingresos − egresos) agrupado por automotriz (VW, Plan Rombo, etc.).

    Detalle importante: la automotriz NO está en el movimiento, cuelga del plan
    de cuentas. Por eso el camino de JOINs es:

        movimientos → planes_cuentas → automotrices

    Y como automotriz_id es NULLABLE (movimientos transversales), uso outerjoin
    (LEFT JOIN): esas filas no se pierden, caen en el grupo
    "Transversal (sin automotriz)".

    OJO conceptual: acá se muestra el FLUJO por automotriz (el neto), no un
    "saldo con inicial incluido". Eso es porque el saldo inicial de hoy es
    global (una sola fila) y todavía no está repartido por automotriz. El día
    que se cargue por automotriz, este es el lugar donde se suma.
    """
    condiciones = [Movimiento.anulado.is_(False)]
    if hasta_fecha is not None:
        condiciones.append(Movimiento.fecha <= hasta_fecha)

    consulta = (
        select(
            Automotriz.nombre,
            func.coalesce(func.sum(Movimiento.ingresos), 0).label("ingresos"),
            func.coalesce(func.sum(Movimiento.egresos), 0).label("egresos"),
        )
        .select_from(Movimiento)
        .join(PlanCuenta, Movimiento.plan_cuenta_id == PlanCuenta.id)
        .outerjoin(Automotriz, PlanCuenta.automotriz_id == Automotriz.id)
        .where(*condiciones)
        .group_by(Automotriz.nombre)
        .order_by(Automotriz.nombre)
    )

    resultado = []
    for nombre, ingresos, egresos in session.execute(consulta):
        ingresos = Decimal(ingresos)
        egresos = Decimal(egresos)
        resultado.append({
            "automotriz": nombre if nombre is not None else "Transversal (sin automotriz)",
            "ingresos": ingresos,
            "egresos": egresos,
            "neto": ingresos - egresos,
        })
    return resultado


# ---------------------------------------------------------------------------
# Saldo por período
# ---------------------------------------------------------------------------

def saldo_por_periodo(session: Session, hasta_fecha: date | None = None) -> list[dict]:
    """
    Ingresos, egresos y neto agrupados por período (anio, mes), en orden
    cronológico, con un saldo ACUMULADO que arrastra el saldo inicial.

    O sea: cada fila trae cuánto se movió ese período (neto) y en qué saldo
    quedó la caja al terminarlo (saldo_acumulado). La última fila con período
    real tiene que darte el mismo número que `saldo_general`.

    Nota: los movimientos sin período (periodo_id NULL) se agrupan aparte, con
    anio/mes = None. Postgres los ordena al final, así que igual quedan sumados
    en el acumulado total (no se pierde plata), solo hay que mostrarlos aparte.
    """
    condiciones = [Movimiento.anulado.is_(False)]
    if hasta_fecha is not None:
        condiciones.append(Movimiento.fecha <= hasta_fecha)

    consulta = (
        select(
            Periodo.anio,
            Periodo.mes,
            func.coalesce(func.sum(Movimiento.ingresos), 0).label("ingresos"),
            func.coalesce(func.sum(Movimiento.egresos), 0).label("egresos"),
        )
        .select_from(Movimiento)
        .outerjoin(Periodo, Movimiento.periodo_id == Periodo.id)
        .where(*condiciones)
        .group_by(Periodo.anio, Periodo.mes)
        .order_by(Periodo.anio, Periodo.mes)
    )

    saldo_inicial = obtener_saldo_inicial(session)
    acumulado = saldo_inicial  # arrancamos desde el saldo inicial
    resultado = []
    for anio, mes, ingresos, egresos in session.execute(consulta):
        ingresos = Decimal(ingresos)
        egresos = Decimal(egresos)
        neto = ingresos - egresos
        acumulado += neto  # el acumulado se arrastra período a período
        resultado.append({
            "anio": anio,
            "mes": mes,
            "ingresos": ingresos,
            "egresos": egresos,
            "neto": neto,
            "saldo_acumulado": acumulado,
        })
    return resultado


# ---------------------------------------------------------------------------
# Prueba rápida (solo se ejecuta si corrés este archivo directo)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Prueba de humo. Correr DESDE LA RAÍZ del proyecto con:
    #
    #     py -m app.logica.saldos
    #
    # (el "-m" es para que Python encuentre los imports "app.database...".
    #  Si lo corrés como "py app/logica/saldos.py" esos imports fallan.)
    with SessionLocal() as session:
        t = totales_generales(session)
        print("=== SALDO GENERAL ===")
        print(f"Saldo inicial : {t['saldo_inicial']:>20,.2f}")
        print(f"Ingresos      : {t['ingresos']:>20,.2f}")
        print(f"Egresos       : {t['egresos']:>20,.2f}")
        print(f"SALDO FINAL   : {t['saldo_final']:>20,.2f}")
        print("  (tendría que dar 4,613,352,569.94)")

        print("\n=== POR AUTOMOTRIZ (neto del flujo) ===")
        for fila in saldo_por_automotriz(session):
            print(f"  {fila['automotriz']:<32} {fila['neto']:>20,.2f}")

        print("\n=== POR PERÍODO ===")
        for fila in saldo_por_periodo(session):
            anio = fila["anio"] if fila["anio"] is not None else "----"
            mes = f"{fila['mes']:02d}" if fila["mes"] is not None else "--"
            print(f"  {anio}-{mes}  neto={fila['neto']:>16,.2f}  acum={fila['saldo_acumulado']:>20,.2f}")
