"""
Test de imports progresivo: importar cada módulo y reportar si funciona.

Uso: python test_imports.py
"""

import sys
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent))

print("Importando módulos paso a paso...\n")

# 1. Verificar que app es un paquete
print("1. Verificar paquete 'app'...")
try:
    import app
    print("   ✓ import app")
except Exception as e:
    print(f"   ✗ FALLO: {e}")
    sys.exit(1)

# 2. Verificar database
print("\n2. Verificar 'app.database'...")
try:
    import app.database
    print("   ✓ import app.database")
except Exception as e:
    print(f"   ✗ FALLO: {e}")

# 3. Verificar models (puede fallar por BD no conectada)
print("\n3. Verificar 'app.database.models'...")
try:
    from app.database import models
    print("   ✓ from app.database import models")
    print(f"      Base: {models.Base}")
except Exception as e:
    print(f"   ✗ FALLO: {e}")

# 4. Verificar conexion
print("\n4. Verificar 'app.database.conexion'...")
try:
    from app.database import conexion
    print("   ✓ from app.database import conexion")
except Exception as e:
    print(f"   ✗ FALLO: {e}")

# 5. Verificar logica
print("\n5. Verificar 'app.logica'...")
try:
    import app.logica
    print("   ✓ import app.logica")
except Exception as e:
    print(f"   ✗ FALLO: {e}")

# 6. Verificar auth
print("\n6. Verificar 'app.logica.auth'...")
try:
    from app.logica import auth
    print("   ✓ from app.logica import auth")
except Exception as e:
    print(f"   ✗ FALLO: {e}")
    import traceback
    traceback.print_exc()

# 7. Verificar sesion
print("\n7. Verificar 'app.logica.sesion'...")
try:
    from app.logica import sesion
    print("   ✓ from app.logica import sesion")
except Exception as e:
    print(f"   ✗ FALLO: {e}")

# 8. Verificar ui
print("\n8. Verificar 'app.ui'...")
try:
    import app.ui
    print("   ✓ import app.ui")
except Exception as e:
    print(f"   ✗ FALLO: {e}")

# 9. Verificar ventana_login
print("\n9. Verificar 'app.ui.ventana_login'...")
try:
    from app.ui import ventana_login
    print("   ✓ from app.ui import ventana_login")
except Exception as e:
    print(f"   ✗ FALLO: {e}")
    import traceback
    traceback.print_exc()

# 10. Verificar main_window
print("\n10. Verificar 'app.ui.main_window'...")
try:
    from app.ui import main_window
    print("   ✓ from app.ui import main_window")
except Exception as e:
    print(f"   ✗ FALLO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETADO")
print("=" * 60)
print("\nSi todos los imports OK, la app debería levantarse con:")
print("  python app/main.py")
