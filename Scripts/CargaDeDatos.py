import pandas as pd
import sqlite3
import logging
import os

# 1. Configuración de Rutas y Logs (Estructura DataOps del Proyecto)
RUTA_ENTRADA = 'Data/Processed/Validation/03_Validacion.csv' 
DB_NAME = 'Data/Sql/db_telco_churn.sqlite'
LOG_CARGA = 'Data/Logs/04_Carga_Datos.log'

# Asegura la existencia de las carpetas necesarias antes de iniciar
os.makedirs("Data/Logs", exist_ok=True)
os.makedirs("Data/Sql", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Etapa 4 - Carga]: %(message)s',
    handlers=[logging.FileHandler(LOG_CARGA, mode='w', encoding="utf-8"), logging.StreamHandler()]
)

def cargar_datos():
    if not os.path.exists(RUTA_ENTRADA):
        logging.error(f"No se encontró el archivo de datos validados en: {RUTA_ENTRADA}")
        return

    # 2. Conexión y Creación de Tabla (Garantiza Reproducibilidad)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Creamos la tabla según campos del CSV
    # Se añade customerID como Clave Primaria (PRIMARY KEY) para evitar duplicados en la base de datos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes_churn (
        customerID TEXT PRIMARY KEY,
        gender TEXT,
        SeniorCitizen TEXT,
        Partner TEXT,
        Dependents TEXT,
        tenure INTEGER,
        PhoneService TEXT,
        MultipleLines TEXT,
        InternetService TEXT,
        OnlineSecurity TEXT,
        OnlineBackup TEXT,
        DeviceProtection TEXT,
        TechSupport TEXT,
        StreamingTV TEXT,
        StreamingMovies TEXT,
        Contract TEXT,
        PaperlessBilling TEXT,
        PaymentMethod TEXT,
        MonthlyCharges REAL,
        TotalCharges REAL,
        Churn TEXT
    )
    """)
    conn.commit()

    # 3. Carga de datos validados desde la etapa previa
    df = pd.read_csv(RUTA_ENTRADA)
    exitos = 0
    rechazados = 0
    
    logging.info(f"Iniciando carga por lotes (Batch) de {len(df)} registros a SQLite...")

    query_insert = """
        INSERT OR REPLACE INTO clientes_churn (
            customerID, gender, SeniorCitizen, Partner, Dependents, tenure, 
            PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup, 
            DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract, 
            PaperlessBilling, PaymentMethod, MonthlyCharges, TotalCharges, Churn
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for i, fila in df.iterrows():
        try:
            # Convertimos la fila del DataFrame a tupla posicional para prevenir inyecciones SQL
            fila_tuple = tuple(fila)
            
            cursor.execute(query_insert, fila_tuple)
            exitos += 1
            
        except sqlite3.IntegrityError as e:
            # Captura violaciones de clave primaria si el cliente ya existe en el Data
            logging.error(f"RECHAZADO - Registro Fila {i} (ID: {fila['customerID']}): Error de integridad (Duplicado) -> {e}")
            rechazados += 1
        except Exception as e:
            # Captura cualquier otra anomalía inesperada de tipado o base de datos
            logging.error(f"RECHAZADO - Registro Fila {i} (ID: {fila['customerID']}): Error inesperado -> {e}")
            rechazados += 1

    # Confirmamos los cambios de la transacción y cerramos la conexión de forma limpia
    conn.commit()
    conn.close()

    # 4. Resumen final del proceso (Métricas analíticas de control para el reporte)

    logging.info("PROCESO DE PERSISTENCIA FINALIZADO.")
    logging.info(f"Registros insertados exitosamente en la DB: {exitos}")
    logging.info(f"Registros rechazados por la Compuerta de Calidad: {rechazados}")


if __name__ == "__main__":
    cargar_datos()