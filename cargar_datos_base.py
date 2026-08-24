"""
cargar_datos_base.py
=====================
Siembra los datos "base" del sistema: los valores fijos que casi no cambian y
sobre los que después se apoya toda la carga del Excel.

Carga:
  - PARTIDAS          (primer nivel: INGRESOS / EGRESOS / SALDO INICIAL)
  - TIPOS DE OPERACIÓN (Transferencia, BtoB, etc.)
  - AUTOMOTRICES      (VW, Plan Rombo, etc.)
  - un USUARIO por defecto ("Sistema") para atribuir la carga histórica.

Todos los valores fueron extraídos de la hoja "4. Plan_cuentas" del Excel real
(no de suposiciones).

El script es IDEMPOTENTE: podés correrlo las veces que quieras y no duplica nada.
Si un valor ya existe, lo saltea; si falta, lo crea.

Correr desde la raíz del proyecto:  py cargar_datos_base.py
"""

from app.database.conexion import SessionLocal
from app.database.models import Partida, TipoOperacion, Automotriz, Usuario


# ---------------------------------------------------------------------------
# Datos a sembrar (extraídos del Excel: hoja "4. Plan_cuentas")
# ---------------------------------------------------------------------------

# (nombre, tipo). El "tipo" define si la partida suma como cobro o como pago.
# NOTA: NO incluimos "SALDO INICIAL" como partida. El saldo inicial no se
# clasifica (no es un cobro ni un pago): se guarda aparte en la tabla
# saldos_iniciales y el saldo se calcula a partir de él.
PARTIDAS = [
    ("INGRESOS", "cobro"),
    ("EGRESOS", "pago"),
]

# Tipos de operación reales (los 5 no vacíos que aparecen en el Excel).
TIPOS_OPERACION = [
    "BtoB",
    "DDJJ",
    "Pagos Bco. Provincia",
    "Transferencia",
    "VEP",
]

# Automotrices: el nombre completo tal cual el Excel. El "código" lo sacamos
# del número que va adelante (ej: "1 - VW - Volkswagen" -> código "1").
AUTOMOTRICES = [
    "1 - VW - Volkswagen",
    "2 - PR - Plan Rombo",
    "3 - GM - Chevrolet",
    "4 - FCA - Fiat",
    "5 - YAM - Yamaha",
    "6 - FCAtr - Fiat Transf.",
    "7 - PRtr - Plan Rombo Transf.",
]

# Usuario por defecto para atribuir los movimientos importados del Excel.
USUARIOS = ["Sistema"]


# ---------------------------------------------------------------------------
# Utilidad: "buscar o crear" (garantiza idempotencia)
# ---------------------------------------------------------------------------
def obtener_o_crear(sesion, modelo, filtro: dict, valores: dict):
    """
    Busca una fila del 'modelo' que cumpla 'filtro'.
      - Si existe, la devuelve y avisa que NO la creó.
      - Si no existe, la crea con 'valores', la agrega a la sesión y avisa que SÍ.

    Devuelve una tupla (objeto, fue_creado).
    """
    obj = sesion.query(modelo).filter_by(**filtro).one_or_none()
    if obj is not None:
        return obj, False
    obj = modelo(**valores)
    sesion.add(obj)
    return obj, True


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main():
    creados = 0

    # Abrimos una sesión (conversación con la base). El 'with' la cierra sola.
    with SessionLocal() as sesion:

        # --- Partidas -------------------------------------------------------
        for nombre, tipo in PARTIDAS:
            _, nuevo = obtener_o_crear(
                sesion, Partida,
                filtro={"nombre": nombre},
                valores={"nombre": nombre, "tipo": tipo},
            )
            if nuevo:
                creados += 1

        # --- Tipos de operación --------------------------------------------
        for nombre in TIPOS_OPERACION:
            _, nuevo = obtener_o_crear(
                sesion, TipoOperacion,
                filtro={"nombre": nombre},
                valores={"nombre": nombre},
            )
            if nuevo:
                creados += 1

        # --- Automotrices ---------------------------------------------------
        for nombre in AUTOMOTRICES:
            # El código es el número antes del primer " - ".
            codigo = nombre.split(" - ")[0].strip()
            _, nuevo = obtener_o_crear(
                sesion, Automotriz,
                filtro={"codigo": codigo},
                valores={"codigo": codigo, "nombre": nombre},
            )
            if nuevo:
                creados += 1

        # --- Usuario por defecto -------------------------------------------
        for nombre in USUARIOS:
            _, nuevo = obtener_o_crear(
                sesion, Usuario,
                filtro={"nombre": nombre},
                valores={"nombre": nombre},
            )
            if nuevo:
                creados += 1

        # Confirmamos TODO junto. Si algo falla antes, no se guarda nada a medias.
        sesion.commit()

        # --- Resumen para el usuario ---------------------------------------
        print(f"✓ Datos base cargados. Filas nuevas creadas en esta corrida: {creados}")
        print("  Totales en la base:")
        print(f"    Partidas:      {sesion.query(Partida).count()}")
        print(f"    Tipos de op.:  {sesion.query(TipoOperacion).count()}")
        print(f"    Automotrices:  {sesion.query(Automotriz).count()}")
        print(f"    Usuarios:      {sesion.query(Usuario).count()}")


if __name__ == "__main__":
    main()
