"""
Debug completo: mostrar paths, estructura, y por qué no encuentra 'app'.

Usa: python debug_completo.py
"""

import sys
import os
from pathlib import Path

print("=" * 80)
print("DEBUG COMPLETO — Cash Flow Autos")
print("=" * 80)

# 1. Python info
print("\n1. INFORMACIÓN DE PYTHON")
print(f"   Versión: {sys.version}")
print(f"   Ejecutable: {sys.executable}")

# 2. Directorio actual
print("\n2. DIRECTORIO ACTUAL")
cwd = os.getcwd()
print(f"   CWD: {cwd}")

# 3. sys.path
print("\n3. sys.path (dónde Python busca módulos)")
for i, path in enumerate(sys.path):
    print(f"   [{i}] {path}")

# 4. ¿Dónde está este script?
print("\n4. UBICACIÓN DE ESTE SCRIPT")
script_dir = Path(__file__).parent.absolute()
print(f"   Script está en: {script_dir}")

# 5. ¿Existe la carpeta 'app'?
print("\n5. ¿EXISTE CARPETA 'app'?")
app_dir = Path(cwd) / "app"
if app_dir.exists():
    print(f"   ✓ app/ existe en: {app_dir}")
    print(f"   ✓ Es directorio: {app_dir.is_dir()}")
else:
    print(f"   ✗ app/ NO existe en: {app_dir}")
    print(f"   Buscando en otras ubicaciones...")
    for base in [Path.cwd(), Path(__file__).parent, Path("/")]:
        search = base / "app"
        if search.exists():
            print(f"      ✓ Encontrada en: {search}")

# 6. ¿Existe app/__init__.py?
print("\n6. ¿EXISTE app/__init__.py?")
init_file = app_dir / "__init__.py"
if init_file.exists():
    print(f"   ✓ __init__.py existe")
    print(f"   ✓ Tamaño: {init_file.stat().st_size} bytes")
    # Ver contenido
    with open(init_file) as f:
        content = f.read()
    print(f"   Contenido: {repr(content[:100])}")
else:
    print(f"   ✗ __init__.py NO existe")
    print(f"   Esperado en: {init_file}")

# 7. Contenido de la carpeta app/
print("\n7. CONTENIDO DE app/")
if app_dir.exists():
    try:
        items = sorted(app_dir.iterdir())
        for item in items:
            if item.is_dir():
                print(f"   [DIR]  {item.name}/")
            else:
                print(f"   [FILE] {item.name}")
    except Exception as e:
        print(f"   ✗ Error al leer: {e}")
else:
    print(f"   ✗ app/ no existe, no se puede listar")

# 8. Intentar agregar app al path y luego importar
print("\n8. INTENTO DE IMPORTACIÓN MANUAL")
try:
    # Agregar cwd al path si no está
    if str(cwd) not in sys.path:
        print(f"   Agregando {cwd} a sys.path...")
        sys.path.insert(0, str(cwd))
    
    # Intentar import
    print(f"   Intentando: import app...")
    import app
    print(f"   ✓ import app OK")
    print(f"   app.__file__ = {app.__file__}")
except Exception as e:
    print(f"   ✗ FALLO: {e}")
    import traceback
    traceback.print_exc()

# 9. Intentar desde app/main.py directamente
print("\n9. VERIFICAR CONTENIDO DE app/main.py")
main_file = app_dir / "main.py"
if main_file.exists():
    print(f"   ✓ main.py existe")
    with open(main_file) as f:
        lines = f.readlines()
    print(f"   Primeras 10 líneas:")
    for i, line in enumerate(lines[:10], 1):
        print(f"      {i}: {line.rstrip()}")
else:
    print(f"   ✗ main.py NO existe en {main_file}")

# 10. RECOMENDACIÓN
print("\n" + "=" * 80)
print("RECOMENDACIÓN")
print("=" * 80)

if not app_dir.exists():
    print("\n✗ PROBLEMA: No se encuentra la carpeta 'app'")
    print("  Solución: Asegúrate de estar en el directorio correcto")
    print(f"           o copia la carpeta 'app/' a: {cwd}")
elif not init_file.exists():
    print("\n✗ PROBLEMA: app/__init__.py no existe")
    print("  Solución: Crear archivo vacío en app/__init__.py")
else:
    print("\n✓ Estructura parece OK")
    print("  Intenta uno de estos:")
    print(f"    cd {cwd} && python app/main.py")
    print(f"    python -m app.main")
    print(f"    python {script_dir}/debug_completo.py")

print("\n" + "=" * 80)
