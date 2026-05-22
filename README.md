# CoLiving Recommender – TFG Ricard Bosch

Sistema de recomendación multi-criterio para pisos compartidos.

## Estructura del proyecto

```
tfg_coliving/
├── models/
│   └── models.py          # Entidades: Candidate, Listing, Household
├── database/
│   └── db.py              # Capa SQLite (CRUD)
├── engine/
│   └── recommender.py     # Motor de recomendación (hard + soft constraints)
├── api/
│   └── main.py            # API REST con FastAPI
├── frontend/
│   └── app.py             # Prototipo web con Streamlit
├── data/
│   └── seed.py            # Dataset sintético (30 candidatos, 20 pisos)
├── database/
│   └── coliving.db        # SQLite (se genera automáticamente)
└── requirements.txt
```

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### 1. Poblar la base de datos con datos sintéticos
```bash
python data/seed.py
```

### 2. Lanzar el frontend Streamlit (demostrador)
```bash
cd frontend
streamlit run app.py
```

### 3. Lanzar la API FastAPI
```bash
cd api
uvicorn main:app --reload
# Documentación interactiva: http://localhost:8000/docs
```

## Endpoints principales de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/candidates` | Listar candidatos |
| POST | `/candidates` | Crear candidato |
| GET | `/listings` | Listar pisos |
| POST | `/listings` | Crear piso |
| GET | `/households` | Listar hogares |
| POST | `/households` | Crear hogar |
| GET | `/recommend/listings/{candidate_id}` | Pisos recomendados para candidato |
| GET | `/recommend/candidates/{listing_id}` | Candidatos recomendados para hogar |
| GET | `/barrios` | Lista de barrios de Barcelona |

## Arquitectura del motor de recomendación

El sistema funciona en **dos fases**:

### Fase 1 – Hard Constraints (filtros obligatorios)
Se descartan pisos que NO cumplan:
- Presupuesto del candidato ≥ precio del piso
- Barrio del piso ∈ barrios preferidos del candidato
- Duración deseada ≥ duración mínima del piso
- Política de fumadores compatible
- Plazas disponibles ≥ 1

### Fase 2 – Soft Scoring (compatibilidad multi-criterio)
Se calcula un score ponderado (0–1) sobre 6 criterios:

| Criterio | Peso |
|----------|------|
| Estilo de convivencia | 30% |
| Tolerancia al ruido | 20% |
| Horario | 15% |
| Duración | 15% |
| Edad | 10% |
| Ocupación | 10% |

El sistema genera además una **explicación en lenguaje natural** de cada recomendación.

## Dataset sintético
- 30 candidatos con perfiles variados (estudiantes, trabajadores, freelances)
- 20 pisos en distintos barrios de Barcelona
- 20 hogares asociados a los pisos con preferencias definidas
