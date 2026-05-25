# Modelo Predictivo de Churn de Clientes

Este proyecto implementa un pipeline de procesamiento y validación de datos orientado a la predicción de abandono de clientes (*Customer Churn*). El sistema permite identificar clientes con mayor probabilidad de cancelar un servicio, apoyando estrategias de retención y análisis de comportamiento.

El proyecto trabaja sobre un dataset de clientes de telecomunicaciones, aplicando procesos de ingesta, limpieza, validación y carga de datos utilizando Python y herramientas de análisis de datos.

---

## Componentes principales del sistema

### 1. Pipeline de procesamiento de datos
El sistema está compuesto por un flujo de procesamiento dividido en varias etapas:

- Ingesta de datos desde archivos CSV.
- Limpieza y transformación de datos.
- Validación de estructura y calidad.
- Carga de datos procesados.
- Generación de logs de ejecución.

### 2. Scripts de procesamiento
Los scripts principales automatizan cada etapa del pipeline:

| Script | Función |
|--------|----------|
| `Ingesta.py` | Lectura y extracción de datos |
| `LimpiezaTransformacion.py` | Limpieza y transformación del dataset |
| `Validacion.py` | Validación de estructura y calidad |
| `CargaDeDatos.py` | Carga y almacenamiento de datos procesados |
| `Pipeline.py` | Ejecución completa del flujo automatizado |

### 3. Gestión de datos
El proyecto organiza la información en distintas capas:

- `Data/Raw/` → Datos originales.
- `Data/Processed/` → Datos procesados.
- `Data/Logs/` → Logs y trazabilidad.
- `Data/Sql/` → Base de datos SQLite.

### 4. Seguridad y trazabilidad
El pipeline incorpora:

- Registro de logs por etapa.
- Identificadores únicos por ejecución.
- Anonimización de datos sensibles mediante SHA-256.

---

## Tecnologías utilizadas

- Python 3.13
- Pandas
- NumPy
- Pandera
- SQLite
- Logging (Python)
- Docker
- Git / GitHub

---

## Contenedorización con Docker

El proyecto incluye soporte para ejecución mediante Docker, permitiendo ejecutar el pipeline completo en un entorno aislado y reproducible.

### Construcción de la imagen

```bash
docker build -t modelo-predictivo-tcc .
```

### Ejecución del contenedor

```bash
docker run --rm modelo-predictivo-tcc
```

---

## Integración continua con GitHub Actions

El proyecto puede automatizar validaciones y ejecuciones del pipeline utilizando GitHub Actions.

### Archivo de workflow

Ubicación:

```bash
.github/workflows/pipeline.yml
```

---

## Pipeline implementado

| Etapa | Descripción |
|-------|-------------|
| 1. Ingesta | Lectura del dataset desde CSV |
| 2. Limpieza | Tratamiento de nulos y normalización |
| 3. Transformación | Conversión y preparación de datos |
| 4. Validación | Verificación de calidad y consistencia |
| 5. Seguridad | Anonimización de datos sensibles |
| 6. Carga | Almacenamiento de datos procesados |
| 7. Logging | Registro y trazabilidad del pipeline |

---

## Estructura del repositorio

```bash
Modelo-Predictivo-TCC/
├── README.md
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── Data/
│   ├── Raw/
│   │   └── 02_Base_WA_Fn-UseC_-Telco-Customer-Churn.csv
│   ├── Processed/
│   │   ├── Ingesta/
│   │   ├── Processing/
│   │   └── Validation/
│   ├── Logs/
│   │   ├── 01_Ingesta_Datos.log
│   │   ├── 02_Limpieza_Transformacion.log
│   │   ├── 03_Validacion.log
│   │   └── 04_Carga_Datos.log
│   └── Sql/
│       └── db_telco_churn.sqlite
├── Scripts/
│   ├── Ingesta.py
│   ├── LimpiezaTransformacion.py
│   ├── Validacion.py
│   ├── CargaDeDatos.py
│   └── Pipeline.py
└── ModelPredictive/
```

---

## Cómo ejecutar el sistema (sin instalación)

### Ejecutar el pipeline completo

Desde la raíz del proyecto:

```bash
python Scripts/Pipeline.py
```

### Ejecutar etapas individuales

```bash
python Scripts/Ingesta.py
python Scripts/LimpiezaTransformacion.py
python Scripts/Validacion.py
python Scripts/CargaDeDatos.py
```

### Resultados esperados

- Generación de archivos procesados en `Data/Processed/`
- Creación de logs en `Data/Logs/`
- Actualización de la base SQLite en `Data/Sql/`

---

## Documento técnico

La documentación técnica y evidencias del pipeline se encuentran en:


- [Informe Técnico](Docs/Informe_Tecnico_TelcoCustomerChurn.pdf)

---

## Objetivo del proyecto

El objetivo principal es construir un flujo de procesamiento de datos confiable y trazable que permita preparar información de clientes para futuros modelos predictivos orientados a la detección temprana de abandono.

---

## Equipo / Créditos

Proyecto académico desarrollado para el módulo TCC.

Responsables del desarrollo:

- Fabrizio González Rodríguez
- Gary Maldonado Guzman