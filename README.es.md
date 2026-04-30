# 📞 Plataforma de QA Inteligente de Llamadas

> **Proyecto de Tesis — Ingeniería Civil Informática · UNAB Santiago, 2026**
> *Felipe Vergara · felipe.vergara19@gmail.com*

**[🇬🇧 English Version](README.md)**

---

Plataforma de aseguramiento de calidad impulsada por IA para operaciones de cobranza en **Colektia**. El sistema ingesta automáticamente grabaciones de llamadas, las transcribe y las audita contra rúbricas configurables usando **Google Gemini 2.5 Flash**, entregando métricas de QA en tiempo real a través de un dashboard React.

## ✨ Funcionalidades Principales

- **Auditoría Automática con IA** — Evalúa llamadas contra rúbricas dinámicas con criterios, pesos y flags de severidad configurables
- **Procesamiento en Micro-lotes** — La ingesta y la evaluación con IA están completamente desacopladas; un scheduler corre cada 240 minutos para procesar llamadas pendientes en lotes de 100
- **Human-in-the-Loop** — Los analistas pueden aprobar, rechazar o comentar las evaluaciones generadas por la IA
- **Control de Acceso por Roles** — Cuatro roles: Admin, Analista QA, KAM, Cliente
- **Arquitectura Multi-tenant** — Aislamiento de datos por empresa cliente (Sistecredito, Rapicredit, etc.)
- **Dashboard de KPIs en Vivo** — Cobertura %, puntaje promedio de calidad, distribución de estatus y más
- **Rúbricas Flexibles** — Crea rúbricas por empresa y rango de días de mora
- **Ajuste de Prompt** — Actualiza el prompt base de la IA en tiempo real sin redespliegue

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLModel · APScheduler |
| Base de Datos | PostgreSQL |
| IA | Google Gemini 2.5 Flash (vía `google-generativeai`) |
| Frontend | React 18 · Vite · Tailwind CSS |
| Autenticación | JWT (Sprint 3 — en progreso) |

## 🗂️ Estructura del Proyecto

```
Qa_llamadas/
├── backend/
│   ├── main.py          # App FastAPI, endpoints, scheduler (HU05, HU16, HU17…)
│   ├── models.py        # Definición de tablas SQLModel (8 tablas)
│   ├── services.py      # Lógica de auditoría con Gemini + reintentos
│   ├── schemas.py       # Esquemas Pydantic para ingesta
│   └── database.py      # Engine y sesión de base de datos
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── Dashboard.jsx    # Historial de llamadas + KPIs
│       │   ├── CallDetail.jsx   # Detalle completo de auditoría por llamada
│       │   └── Settings.jsx     # Configuración de rúbricas y prompt
│       └── api.js               # Cliente API con Axios
└── ERD_QA_Llamadas.pdf  # Diagrama Entidad-Relación
```

## 🗄️ Esquema de Base de Datos (8 tablas)

| Tabla | Propósito |
|---|---|
| `usuario` | Autenticación y roles (admin / analista_qa / kam / cliente) |
| `cliente` | Empresas clientes con sus guiones de llamada |
| `llamada` | Registros de llamadas con transcripción y metadatos |
| `evaluacion` | Resultados de auditoría IA + campos de validación humana |
| `rubrica` | Rúbricas de evaluación por empresa y rango de mora |
| `criterio` | Criterios individuales de una rúbrica (peso + severidad) |
| `configuracionsistema` | Configuración clave-valor del sistema (prompt base IA, etc.) |
| `guioncliente` | Guiones por cliente — reservada para Sprint 4 (HU25) |

> Ver [`ERD_QA_Llamadas.pdf`](ERD_QA_Llamadas.pdf) para el diagrama entidad-relación completo.

## 🚀 Cómo Ejecutar el Proyecto

### Requisitos Previos

- Python 3.11+
- Node.js 18+
- PostgreSQL corriendo localmente
- Una API key de Google Gemini

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL="postgresql://usuario:contraseña@localhost/qa_llamadas"
export GEMINI_API_KEY="tu-api-key-aqui"

uvicorn main:app --reload
```

API disponible en `http://localhost:8000` · Documentación en `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplicación disponible en `http://localhost:5173`

## 📡 Endpoints Principales de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/v1/llamadas/ingesta` | Ingestar una nueva llamada (desde Colly) |
| `POST` | `/api/v1/auditoria/ejecutar` | Disparar manualmente el batch de auditoría |
| `GET` | `/api/v1/auditoria/estado` | Estado de la cola + próxima ejecución programada |
| `GET` | `/api/v1/llamadas` | Historial completo de llamadas |
| `GET` | `/api/v1/evaluaciones/{id}` | Detalle completo de auditoría de una llamada |
| `GET` | `/api/v1/dashboard` | KPIs globales |
| `GET/POST` | `/api/v1/rubricas` | Listar / crear rúbricas |
| `GET/POST` | `/api/v1/config/prompt` | Obtener / actualizar prompt base de la IA |

## 📋 Progreso de Desarrollo

| Sprint | Fechas | Puntos | Estado |
|---|---|---|---|
| Sprint 1 | 01 Mar – 14 Mar 2026 | 22 pts | ✅ Completado |
| Sprint 2 | 15 Mar – 11 Abr 2026 | 34 pts | ✅ Completado |
| Sprint 3 | 26 Abr – 09 May 2026 | 26 pts | 🔄 En Curso |
| Sprint 4 | 10 May – 16 May 2026 | 21 pts | ⏳ Pendiente |
| Sprint 5 | 17 May – 19 May 2026 | 18 pts | ⏳ Entrega Final |

## 📄 Licencia

Proyecto académico — Universidad Andrés Bello (UNAB), Santiago, Chile.
No licenciado para uso comercial.
