# Cash Flow Autos

Sistema de escritorio para gestionar el flujo de fondos (cobros y pagos) de
un sector de la empresa. Reemplaza el Excel actual, con una base de datos
central en la nube para que varias personas trabajen desde distintas PCs de
la oficina sin perder trazabilidad ni depender de un servidor físico.

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Licencia](https://img.shields.io/badge/uso-interno-lightgrey)

---

## Qué hace

- Carga de **cobros** y **pagos**, con cuenta, categoría y comprobante.
- Cálculo de **saldos** en tiempo real por cuenta y saldo general.
- Ningún movimiento se borra: los errores se corrigen con una anulación que
  queda registrada, así el historial completo nunca se pierde.
- **Reportes** por período, cuenta y categoría.
- **Exportación a Excel** de movimientos y reportes, para seguir compartiendo
  información con quien lo necesite en el formato de siempre.
- Varias personas pueden usarlo al mismo tiempo desde distintas PCs de la
  oficina.

---

## Capturas

> _Se completa con imágenes reales una vez armada la UI._

| Pantalla principal | Carga de movimiento | Reportes |
|---|---|---|
| `(captura pendiente)` | `(captura pendiente)` | `(captura pendiente)` |

---

## Stack

| Capa | Tecnología |
|---|---|
| Interfaz de escritorio | Python + PySide6 (Qt) |
| Base de datos | PostgreSQL, hosteado en Neon |
| Acceso a datos | SQLAlchemy + psycopg2 |
| Migraciones de esquema | Alembic |
| Exportación a Excel | openpyxl |
| Distribución | PyInstaller (.exe) |

Más detalle de arquitectura y decisiones en [`specs.md`](./specs.md).

---

## Instalación (para desarrollo)

Requisitos: Python 3.12 o superior instalado.

```bash
# 1. Clonar el proyecto
git clone <url-del-repositorio>
cd cash-flow-autos

# 2. Crear un entorno virtual
python -m venv venv
venv\Scripts\activate        # en Windows
# source venv/bin/activate   # en Mac/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar la conexión a la base de datos
copy .env.example .env       # en Windows
# cp .env.example .env       # en Mac/Linux
# Completar .env con el connection string de Neon (ver sección siguiente)

# 5. Aplicar el esquema de base de datos
alembic upgrade head

# 6. Ejecutar la aplicación
python app/main.py
```

### Configurar `.env`

```env
DATABASE_URL=postgresql://usuario:password@host.neon.tech/nombre_db?sslmode=require
```

Este archivo **no se sube al repositorio** — cada persona que instale el
proyecto debe completar el suyo con las credenciales de Neon.

---

## Uso diario (para el equipo, sin instalar Python)

Para el día a día en la oficina, no hace falta instalar Python ni nada
técnico: se distribuye un instalador (`.exe`) generado con PyInstaller.

1. Ejecutar `CashFlowAutos.exe` (acceso directo en el escritorio).
2. Iniciar sesión con el usuario asignado.
3. Cargar cobros o pagos desde el menú principal.
4. Los saldos se actualizan automáticamente para todos los que estén
   conectados en ese momento.

---

## Estructura del proyecto

```
cash-flow-autos/
├── app/
│   ├── database/          # Conexión, modelos y migraciones
│   ├── logica/             # Reglas de negocio (movimientos, saldos, reportes)
│   ├── ui/                 # Pantallas de la aplicación (PySide6)
│   ├── utils/               # Exportación a Excel y otras utilidades
│   └── main.py              # Punto de entrada
├── .env.example
├── requirements.txt
├── specs.md                 # Especificación técnica completa
└── README.md
```

---

## Respaldo y recuperación

- Neon mantiene recuperación a un punto en el tiempo (ventana de 6 horas en
  el plan gratuito).
- Se complementa con un backup diario automático hacia la carpeta compartida
  de la oficina, para poder volver a estados de hace varios días si hiciera
  falta.

Detalle completo en la sección 7 de [`specs.md`](./specs.md).

---

## Roadmap

- [x] Definición de arquitectura y modelo de datos (`specs.md`)
- [ ] Conexión de prueba a Neon
- [ ] Modelos SQLAlchemy + primera migración
- [ ] Lógica de negocio: alta y anulación de movimientos
- [ ] Pantallas de carga de cobros y pagos
- [ ] Reportes y exportación a Excel
- [ ] Empaquetado en `.exe` y prueba en una segunda PC
- [ ] Backup automático programado

---

## Notas

Proyecto de uso interno. El código está comentado en español pensando en
alguien que está aprendiendo a programar, no solo en quien lo mantenga a
futuro.
