# probar_conexion.py
# Script mínimo para verificar que podemos conectarnos a Neon.
# Solo lee (SELECT), no crea ni modifica nada en la base.

import os
import psycopg2                      # driver de PostgreSQL para Python
from dotenv import load_dotenv       # para leer el .env

# Carga las variables del archivo .env (entre ellas, DATABASE_URL)
load_dotenv()

# Tomamos el connection string desde el .env, así no queda escrito en el código
connection_string = os.getenv("DATABASE_URL")

if not connection_string:
    # Si falta la variable, avisamos claro en vez de fallar con un error críptico
    print("ERROR: no encontré DATABASE_URL. ¿Completaste el archivo .env?")
    raise SystemExit(1)

try:
    # Abrimos la conexión. El 'with' se encarga de cerrarla al terminar.
    with psycopg2.connect(connection_string) as conexion:
        with conexion.cursor() as cursor:
            # Consulta trivial: le pedimos a Postgres su versión y la hora del server.
            # Consulta trivial: le pedimos a Postgres su versión y la hora del server.
            cursor.execute("SELECT version(), now();")
            fila = cursor.fetchone()   # puede ser una tupla o None

            # Nos aseguramos de que la consulta haya traído algo antes de usarla.
            # (En un SELECT como este siempre trae una fila, pero así Pylance no protesta
            #  y el código queda protegido ante cualquier caso raro.)
            if fila is None:
                print("✗ La consulta no devolvió resultados.")
                raise SystemExit(1)

            version, hora = fila   # ahora sí, seguro que 'fila' tiene dos valores

            print("✓ Conexión exitosa a Neon")
            print(f"  Versión de PostgreSQL: {version}")
            print(f"  Hora del servidor:     {hora}")

except Exception as error:
    # Cualquier problema (credenciales, internet, SSL) cae acá
    print("✗ No pude conectarme. Detalle del error:")
    print(f"  {error}")