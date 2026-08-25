# app/logica/movimientos.py
"""
Lógica de negocio de los MOVIMIENTOS (cobros y pagos).

Este es el primer módulo "de escritura": acá se crean, anulan y corrigen
movimientos. Todo lo que toca la base pasa por acá, para tener las reglas en
un solo lugar (la UI solo llama a estas funciones).

Reglas de oro del proyecto:

  1) El monto SIEMPRE es positivo. Si es ingreso o egreso lo decide la PARTIDA
     del código (cobro -> ingreso, pago -> egreso). El usuario no elige el signo,
     así no se puede cargar un egreso contra un código de ingreso.

  2) NUNCA se borra un movimiento. Para deshacer un error se ANULA:
        - se marca el original con anulado=True
        - se crea un movimiento de REVERSA (montos invertidos), también anulado=True
        - se enlaza el original a su reversa (movimiento_anulacion_id)

     ¿Por qué la reversa también va anulado=True? Porque el saldo se calcula con
     "SUM(ingresos - egresos) WHERE anulado=false" (ver saldos.py). Si la reversa
     quedara anulado=False, descontaría de nuevo lo que el original ya dejó de
     sumar: el saldo bajaría DOS veces. Con ambos en anulado=True el par neutraliza
     al original (aporta 0) y la reversa queda como registro de auditoría: guarda
     QUIÉN anuló y CUÁNDO (dato que el original no tiene).

  3) El saldo nunca se escribe: siempre se recalcula desde los movimientos.

Sobre transacciones: cada función maneja su propia transacción y hace commit al
final (salvo que se pase confirmar=False, para poder encadenar varias en una sola
transacción, como hace corregir_movimiento). Si algo falla, se hace rollback y no
queda nada a medias.
"""

from decimal import Decimal
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.conexion import SessionLocal
from app.database.models import Movimiento, PlanCuenta, Usuario, Periodo


# ---------------------------------------------------------------------------
# Error de negocio
# ---------------------------------------------------------------------------
class ErrorDeNegocio(Exception):
    """
    Error "esperable" por una regla de negocio (código inexistente, monto <= 0,
    usuario inactivo, etc.). La UI lo puede atrapar para mostrar un cartel claro,
    distinto de un error inesperado del programa.
    """
    pass


# ---------------------------------------------------------------------------
# Helpers internos (validaciones y búsquedas)
# ---------------------------------------------------------------------------
def _a_decimal(valor) -> Decimal:
    """
    Convierte un número a Decimal de forma segura.
    Usamos Decimal (no float) porque estamos manejando PLATA: float redondea mal
    (0.1 + 0.2 != 0.3). Pasamos por str() para no arrastrar la imprecisión del float.
    """
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def _resolver_plan_cuenta(session: Session, codigo: int) -> PlanCuenta:
    """Busca el plan de cuentas por su código y valida que exista y esté activo."""
    plan = session.scalar(select(PlanCuenta).where(PlanCuenta.codigo == codigo))
    if plan is None:
        raise ErrorDeNegocio(f"El código {codigo} no existe en el plan de cuentas.")
    if not plan.activo:
        raise ErrorDeNegocio(f"El código {codigo} está inactivo; no se puede usar.")
    return plan


def _validar_usuario(session: Session, usuario_id: int) -> Usuario:
    """Valida que el usuario exista y esté activo."""
    usuario = session.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorDeNegocio(f"El usuario id={usuario_id} no existe.")
    if not usuario.activo:
        raise ErrorDeNegocio(f"El usuario '{usuario.nombre}' está inactivo.")
    return usuario


def buscar_periodo(session: Session, mes: int, anio: int) -> Periodo | None:
    """
    Devuelve el período (mes, anio) si existe, o None.
    Útil para que la UI resuelva el periodo_id a partir de mes/año sin que el
    usuario tenga que saber el id interno.
    """
    return session.scalar(
        select(Periodo).where(Periodo.mes == mes, Periodo.anio == anio)
    )


# ---------------------------------------------------------------------------
# Alta de movimiento
# ---------------------------------------------------------------------------
def crear_movimiento(
    session: Session,
    *,
    codigo: int,
    fecha: date,
    monto,
    usuario_id: int,
    comprobante: str | None = None,
    periodo_id: int | None = None,
    descripcion: str | None = None,
    confirmar: bool = True,
) -> Movimiento:
    """
    Crea un movimiento (cobro o pago) y lo devuelve.

    Parámetros (van con nombre, por el '*' de arriba, para que la llamada se lea
    clara: crear_movimiento(session, codigo=..., fecha=..., monto=...)):
      - codigo: el código del plan de cuentas (ej: 1041131).
      - fecha: fecha del movimiento (date).
      - monto: importe POSITIVO. El signo (ingreso/egreso) lo define la partida.
      - usuario_id: quién lo carga.
      - comprobante, periodo_id, descripcion: opcionales.
      - confirmar: si es True hace commit; si es False deja la transacción abierta
        (para encadenar, ver corregir_movimiento).
    """
    # --- Validaciones ---
    if not isinstance(fecha, date):
        raise ErrorDeNegocio("La fecha debe ser un date válido.")

    monto = _a_decimal(monto)
    if monto <= 0:
        raise ErrorDeNegocio(
            "El monto debe ser mayor a 0 (el signo lo define la partida, no el usuario)."
        )

    plan = _resolver_plan_cuenta(session, codigo)
    _validar_usuario(session, usuario_id)

    # --- Ingreso o egreso: lo decide la PARTIDA del código, no el usuario ---
    tipo = plan.partida.tipo  # 'cobro' o 'pago'
    if tipo == "cobro":
        ingresos, egresos = monto, Decimal("0")
    elif tipo == "pago":
        ingresos, egresos = Decimal("0"), monto
    else:
        # ej: 'saldo_inicial' u otro; esos no se cargan como movimiento normal.
        raise ErrorDeNegocio(
            f"La partida del código {codigo} es '{tipo}': no se puede cargar como movimiento."
        )

    mov = Movimiento(
        fecha=fecha,
        mes=fecha.month,                 # el mes se deriva de la fecha
        plan_cuenta_id=plan.id,
        periodo_id=periodo_id,
        comprobante=comprobante,
        ingresos=ingresos,
        egresos=egresos,
        neto=ingresos - egresos,         # neto siempre coherente con ingresos/egresos
        usuario_id=usuario_id,
        anulado=False,
        descripcion_adicional=descripcion,
    )

    session.add(mov)
    try:
        session.flush()                  # asigna el id y valida las FKs contra la base
        if confirmar:
            session.commit()
    except Exception:
        session.rollback()               # si algo falla, no queda nada a medias
        raise
    return mov


# ---------------------------------------------------------------------------
# Anulación (con reversa enlazada)
# ---------------------------------------------------------------------------
def anular_movimiento(
    session: Session,
    *,
    movimiento_id: int,
    usuario_id: int,
    motivo: str | None = None,
    confirmar: bool = True,
) -> Movimiento:
    """
    Anula un movimiento existente y devuelve la REVERSA creada.

    Pasos (todo en una sola transacción):
      1) Se valida que el original exista y no esté ya anulado.
      2) Se crea la reversa: mismos datos, pero con ingresos/egresos INVERTIDOS
         y anulado=True (así no vuelve a mover el saldo; ver nota del encabezado).
      3) Se marca el original anulado=True y se lo enlaza a la reversa
         (original.movimiento_anulacion_id = reversa.id).

    Efecto en el saldo: original y reversa quedan ambos anulado=True, o sea que
    ninguno suma. El resultado es como si el movimiento nunca hubiera existido,
    pero queda TODO el rastro (original marcado, reversa con quién/cuándo anuló).

    'usuario_id' es quién ANULA (puede ser distinto de quién creó el original).
    """
    original = session.get(Movimiento, movimiento_id)
    if original is None:
        raise ErrorDeNegocio(f"No existe el movimiento id={movimiento_id}.")
    if original.anulado:
        raise ErrorDeNegocio(f"El movimiento id={movimiento_id} ya está anulado.")

    _validar_usuario(session, usuario_id)

    reversa = Movimiento(
        fecha=original.fecha,
        mes=original.mes,
        plan_cuenta_id=original.plan_cuenta_id,
        periodo_id=original.periodo_id,
        comprobante=original.comprobante,
        ingresos=original.egresos,       # <-- invertido: lo que era egreso pasa a ingreso
        egresos=original.ingresos,       # <-- invertido: lo que era ingreso pasa a egreso
        neto=-original.neto,             # neto opuesto al original
        usuario_id=usuario_id,           # quién anula (queda registrado en la reversa)
        anulado=True,                    # documentaria: NO afecta el saldo
        descripcion_adicional=(
            motivo or f"Reversa por anulación del movimiento #{original.id}"
        ),
    )

    session.add(reversa)
    try:
        session.flush()                  # necesitamos reversa.id para poder enlazar
        original.anulado = True
        original.movimiento_anulacion_id = reversa.id
        session.flush()
        if confirmar:
            session.commit()
    except Exception:
        session.rollback()
        raise
    return reversa


# ---------------------------------------------------------------------------
# Corrección (anular + recrear en una sola transacción)
# ---------------------------------------------------------------------------
def corregir_movimiento(
    session: Session,
    *,
    movimiento_id: int,
    usuario_id: int,
    codigo: int,
    fecha: date,
    monto,
    comprobante: str | None = None,
    periodo_id: int | None = None,
    descripcion: str | None = None,
) -> tuple[Movimiento, Movimiento]:
    """
    Caso real de "me equivoqué y quiero corregir": anula el movimiento viejo y
    crea uno nuevo con los datos corregidos, TODO en la misma transacción.

    O pasan las dos cosas juntas, o no pasa ninguna: si la creación del nuevo
    fallara, la anulación del viejo también se deshace (rollback). Así nunca
    queda un movimiento anulado sin su reemplazo.

    Devuelve una tupla (reversa, nuevo).
    """
    try:
        # confirmar=False en las dos: no cerramos la transacción hasta el final
        reversa = anular_movimiento(
            session, movimiento_id=movimiento_id, usuario_id=usuario_id, confirmar=False
        )
        nuevo = crear_movimiento(
            session,
            codigo=codigo,
            fecha=fecha,
            monto=monto,
            usuario_id=usuario_id,
            comprobante=comprobante,
            periodo_id=periodo_id,
            descripcion=descripcion,
            confirmar=False,
        )
        session.commit()                 # un único commit para las dos operaciones
    except Exception:
        session.rollback()
        raise
    return reversa, nuevo


# ---------------------------------------------------------------------------
# Prueba rápida (dry-run: NO guarda nada en la base real)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Esta prueba crea y anula un movimiento de mentira para ver que la lógica
    # corre de punta a punta, pero hace ROLLBACK al final: NO persiste NADA en
    # la base real (que tiene los 2742 movimientos de verdad). Correr con:
    #
    #     py -m app.logica.movimientos
    #
    with SessionLocal() as session:
        try:
            # Tomamos un código y un usuario reales cualquiera para la demo.
            plan = session.scalar(select(PlanCuenta).where(PlanCuenta.activo.is_(True)))
            usuario = session.scalar(select(Usuario).where(Usuario.activo.is_(True)))

            if plan is None or usuario is None:
                print("No hay plan de cuentas o usuario activo para la prueba.")
            else:
                print(
                    f"Usando código {plan.codigo} (partida '{plan.partida.tipo}') "
                    f"y usuario '{usuario.nombre}'.\n"
                )

                mov = crear_movimiento(
                    session,
                    codigo=plan.codigo,
                    fecha=date.today(),
                    monto=Decimal("1000.00"),
                    usuario_id=usuario.id,
                    comprobante="PRUEBA-DRYRUN",
                    confirmar=False,                 # no commiteamos: es un ensayo
                )
                print(
                    f"Se CREARÍA  -> id={mov.id}  ingresos={mov.ingresos}  "
                    f"egresos={mov.egresos}  neto={mov.neto}"
                )

                reversa = anular_movimiento(
                    session,
                    movimiento_id=mov.id,
                    usuario_id=usuario.id,
                    confirmar=False,
                )
                print(
                    f"Reversa     -> id={reversa.id}  ingresos={reversa.ingresos}  "
                    f"egresos={reversa.egresos}  anulado={reversa.anulado}"
                )
                print(
                    f"Original    -> anulado={mov.anulado}  "
                    f"movimiento_anulacion_id={mov.movimiento_anulacion_id}"
                )
                print(
                    f"\nOriginal y reversa se cancelan: {mov.neto} + {reversa.neto} "
                    f"= {mov.neto + reversa.neto}  (y además ambos van anulado=True)"
                )
        finally:
            session.rollback()
            print("\nRollback hecho: no se guardó ningún dato de prueba. ✔")
