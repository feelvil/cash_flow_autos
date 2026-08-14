# Cash Flow Autos — Especificación técnica (v1)

## 1. Resumen del proyecto

Sistema de escritorio para gestionar el flujo de fondos (cobros y pagos) de un
sector de la empresa, reemplazando el Excel actual. Corre en varias PCs de la
oficina (red local) y todas se conectan a una única base de datos en la nube,
para no depender de un servidor físico prendido todo el día.

**Objetivo principal:** poder registrar cada cobro y pago con trazabilidad,
consultar saldos y estados en tiempo real, generar reportes, y tener la
posibilidad de "volver atrás" ante un error sin perder información — algo que
hoy el Excel no garantiza.

**No-objetivos de v1** (quedan para después):
- Acceso remoto fuera de la oficina / app web.
- Notificaciones automáticas (mail, alertas).
- Conciliación bancaria automática.
- App mobile.

---

## 2. Alcance de la v1

Incluye:
- ABM de **cuentas** (caja, banco, etc.)
- ABM de **categorías** de cobro/pago
- Carga de **cobros** y **pagos**
- Cálculo de **saldos** por cuenta y saldo general
- **Reportes** básicos (por período, por categoría, por cuenta)
- **Exportación a Excel** de movimientos y reportes
- Registro de auditoría **básico** (quién y cuándo cargó cada movimiento) —
  ver sección 8 para el detalle de qué queda para v1 y qué para v2.

No incluye en v1:
- Reversas/ajustes con flujo de aprobación (se anota manual por ahora)
- Roles y permisos granulares (todos los usuarios tienen el mismo nivel)
- Multi-sector / multi-empresa

---

## 3. Usuarios y contexto de uso

- Varias personas trabajando desde distintas PCs de la oficina, en red local,
  al mismo tiempo.
- Todos con conocimientos de Excel, no necesariamente técnicos → la UI tiene
  que ser simple e intuitiva, sin jerga técnica.
- Se espera un volumen bajo/medio de movimientos (decenas a un par de
  centenas por día, no miles) — esto es relevante para no sobredimensionar
  infraestructura.

---

## 4. Arquitectura

```
[PC oficina 1]      [PC oficina 2]      [PC oficina 3]
  App Python           App Python           App Python
  (PySide6)            (PySide6)            (PySide6)
       \                    |                    /
        \                   |                   /
         ----------- Internet (HTTPS/SSL) ------
                            |
                  Neon (PostgreSQL en la nube)
                  - Base de datos principal
                  - Point-in-time recovery
```

**Por qué este esquema:**
- No requiere instalar ni mantener un servidor físico en la oficina.
- Neon ofrece recuperación a un punto en el tiempo, que cubre el requisito de
  "poder volver atrás sin perder nada" (con matices, ver sección 7).
- PostgreSQL es gratuito, estándar, y tiene buen soporte en Python.

**Riesgo aceptado:** depende de tener conexión a internet en la oficina. Si
hoy ya se trabaja con internet de forma estable, no es un riesgo nuevo.

---

## 5. Stack tecnológico

| Capa | Tecnología | Motivo |
|---|---|---|
| Lenguaje | Python 3.12+ | Ya conocido por el usuario |
| UI de escritorio | PySide6 (Qt) | Diseño moderno, evita Tkinter, buen soporte de estilos (QSS) |
| Base de datos | PostgreSQL (hosteado en Neon) | Gratis para el volumen esperado, sin servidor propio, con recovery |
| Acceso a datos | SQLAlchemy (ORM) + psycopg2 | Estándar en Python, facilita mantenimiento y migraciones |
| Migraciones de esquema | Alembic | Versionar cambios en las tablas de forma controlada |
| Exportación a Excel | openpyxl | Compatibilidad con el flujo actual en Excel |
| Empaquetado / distribución | PyInstaller | Generar un .exe para instalar en cada PC sin pedir que instalen Python |
| Variables de entorno / config | python-dotenv | Guardar el connection string de forma segura, fuera del código |

**Todo el código va comentado en español**, explicando el porqué de cada
función y bloque relevante, orientado a alguien que está aprendiendo.

---

## 6. Modelo de datos (borrador inicial)

> Este es un punto de partida — se termina de ajustar mirando el Excel actual
> como referencia, en la siguiente etapa del proyecto.

### `cuentas`
| Campo | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| nombre | text | ej: "Caja chica", "Banco Galicia" |
| tipo | text | caja / banco / otro |
| saldo_inicial | numeric(14,2) | |
| activa | boolean | default true |
| creado_en | timestamp | default now() |

### `categorias`
| Campo | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| nombre | text | ej: "Proveedores", "Sueldos", "Ventas" |
| tipo | text | cobro / pago |
| activa | boolean | default true |

### `movimientos`
| Campo | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| tipo | text | 'cobro' o 'pago' |
| fecha | date | |
| cuenta_id | FK → cuentas | |
| categoria_id | FK → categorias | |
| monto | numeric(14,2) | siempre positivo, el signo lo da `tipo` |
| descripcion | text | |
| numero_comprobante | text | opcional |
| usuario_id | FK → usuarios | quién lo cargó |
| creado_en | timestamp | default now() |
| anulado | boolean | default false — nunca se borra, se anula (ver sección 8) |
| movimiento_anulacion_id | FK → movimientos, nullable | referencia al asiento que lo anula, si aplica |

### `usuarios`
| Campo | Tipo | Notas |
|---|---|---|
| id | serial PK | |
| nombre | text | |
| activo | boolean | default true |

---

## 7. Estrategia de respaldo y recuperación

Requisito original: *"si ocurre algo, poder volver atrás y no perder nada"*.
Se cubre en dos niveles:

1. **Point-in-time recovery de Neon**: en el plan gratis, la ventana de
   recuperación es de 6 horas. Sirve para errores detectados el mismo día.
2. **Backup propio adicional**: un script en Python programado (tarea
   programada de Windows) que exporta la base completa a un archivo, una vez
   por día, a la carpeta compartida. Esto cubre el caso de necesitar volver a
   un estado de hace varios días, algo que el plan gratis de Neon no
   garantiza.

Si el volumen de movimientos justifica pasar a un plan pago de Neon más
adelante, se extiende la ventana de recovery y se puede reducir la
dependencia del backup manual. El costo esperado es bajo dado el volumen de
uso.

---

## 8. Auditoría (trazabilidad de cambios)

Definida como **importante pero no bloqueante** para el MVP. Se implementa en
dos etapas:

**v1 (incluido en este alcance):**
- Cada movimiento guarda quién lo creó (`usuario_id`) y cuándo
  (`creado_en`).
- Ningún movimiento se borra físicamente: para corregir un error, se marca el
  original como `anulado` y se crea un nuevo movimiento de reversa
  enlazado (`movimiento_anulacion_id`). El historial completo queda
  siempre disponible.

**v2 (futuro, fuera de este alcance):**
- Tabla de log genérica que registre también modificaciones a cuentas y
  categorías, no solo movimientos.
- Registro de qué campos específicos cambiaron en cada edición (before/after).

---

## 9. Estructura de carpetas propuesta

```
cash-flow-autos/
├── app/
│   ├── database/
│   │   ├── models.py         # Modelos SQLAlchemy (tablas)
│   │   ├── conexion.py       # Conexión a Neon
│   │   └── migraciones/      # Alembic
│   ├── logica/
│   │   ├── movimientos.py    # Reglas de negocio: alta, anulación, validaciones
│   │   ├── saldos.py         # Cálculo de saldos por cuenta
│   │   └── reportes.py       # Armado de reportes
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── pantalla_cobros.py
│   │   ├── pantalla_pagos.py
│   │   ├── pantalla_reportes.py
│   │   └── estilos.qss       # Hoja de estilos para diseño moderno
│   ├── utils/
│   │   └── exportar_excel.py
│   └── main.py                # Punto de entrada de la app
├── .env                        # Connection string (no se sube a git)
├── .env.example
├── requirements.txt
├── specs.md                    # Este documento
└── README.md
```

---

## 10. Roadmap sugerido

1. **Setup inicial**: crear proyecto en Neon, probar conexión desde un script
   simple de Python (INSERT/SELECT de prueba).
2. **Modelo de datos definitivo**: ajustar las tablas de la sección 6 mirando
   el Excel actual como referencia real.
3. **Capa de base de datos**: modelos SQLAlchemy + primera migración con
   Alembic.
4. **Lógica de negocio**: alta de movimientos, cálculo de saldos, anulación.
5. **UI mínima**: pantalla de carga de cobros/pagos + vista de saldo.
6. **Reportes y exportación a Excel**.
7. **Empaquetado**: generar el .exe con PyInstaller y probarlo en una segunda
   PC de la oficina.
8. **Backup automático**: script + tarea programada.

---

## 11. Preguntas abiertas para la siguiente etapa

- [ ] Revisar el Excel actual: ¿qué columnas tiene exactamente cada hoja?
- [ ] ¿Hay más de una cuenta (banco/caja) hoy en el Excel, o es una sola?
- [ ] ¿Los reportes se necesitan por mes, por semana, ambos?
- [ ] ¿Cuántas personas van a usar el sistema en simultáneo aproximadamente?
