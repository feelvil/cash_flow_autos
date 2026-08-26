"""
Script de diagnóstico: verificar que todos los módulos se importan correctamente.

Uso: python diagnostico.py
"""

import sys
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("DIAGNÓSTICO DE IMPORTS — Cash Flow Autos")
print("=" * 70)

# Test 1: Paquete principal
print("\n1. Importando paquete 'app'...")
try:
    import app
    print("   ✓ OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    sys.exit(1)

# Test 2: Database
print("\n2. Importando 'app.database'...")
try:
    from app.database import models, conexion
    print("   ✓ models.py OK")
    print("   ✓ conexion.py OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 3: Lógica
print("\n3. Importando 'app.logica'...")
try:
    from app.logica import auth, sesion, saldos, catalogos, movimientos, reportes
    print("   ✓ auth.py OK")
    print("   ✓ sesion.py OK")
    print("   ✓ saldos.py OK")
    print("   ✓ catalogos.py OK")
    print("   ✓ movimientos.py OK")
    print("   ✓ reportes.py OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    print(f"\n   Traceback completo:")
    import traceback
    traceback.print_exc()

# Test 4: UI
print("\n4. Importando 'app.ui'...")
try:
    from app.ui import ventana_login
    print("   ✓ ventana_login.py OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    print(f"\n   Traceback completo:")
    import traceback
    traceback.print_exc()

# Test 5: Utils
print("\n5. Importando 'app.utils'...")
try:
    from app.utils import exportar_excel
    print("   ✓ exportar_excel.py OK")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# Test 6: PySide6
print("\n6. Verificando dependencias externas...")
try:
    import PySide6
    print("   ✓ PySide6 instalado")
except:
    print("   ✗ PySide6 NO instalado")
    print("      Solución: pip install PySide6")

try:
    import sqlalchemy
    print("   ✓ SQLAlchemy instalado")
except:
    print("   ✗ SQLAlchemy NO instalado")
    print("      Solución: pip install SQLAlchemy")

try:
    import bcrypt
    print("   ✓ bcrypt instalado")
except:
    print("   ✗ bcrypt NO instalado")
    print("      Solución: pip install bcrypt")

try:
    import dotenv
    print("   ✓ python-dotenv instalado")
except:
    print("   ✗ python-dotenv NO instalado")
    print("      Solución: pip install python-dotenv")

# Test 7: Archivo .env
print("\n7. Verificando .env...")
env_path = project_root / ".env"
if env_path.exists():
    print(f"   ✓ .env existe en {env_path}")
    # Verificar que tiene DATABASE_URL
    with open(env_path) as f:
        content = f.read()
        if "DATABASE_URL" in content:
            print("   ✓ DATABASE_URL configurado")
        else:
            print("   ✗ DATABASE_URL NO configurado en .env")
else:
    print(f"   ✗ .env NO existe en {env_path}")
    print("      Solución: crear .env con DATABASE_URL")

print("\n" + "=" * 70)
print("FIN DEL DIAGNÓSTICO")
print("=" * 70)
