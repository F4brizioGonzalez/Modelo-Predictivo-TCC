import pandas as pd
import numpy as np
import logging
import uuid
import hashlib

# Definir la ruta del archivo CSV a procesar
ruta_csv = "Data/Processed/Ingesta/01_Extraccion_Datos.csv"

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Etapa 2 - Limpieza y Transformación]: %(message)s',
    handlers=[
        logging.FileHandler("Data/Logs/01_Limpieza_Transformacion.log"),
        logging.StreamHandler()
    ]
)

# Fase de seguridad para la gestión de datos sensibles
# Aplicando anonimización según Ley 19.719 (Sha-256)
def encryptar_customerID(customerID):
    return hashlib.sha256(str(customerID).encode()).hexdigest()

# Etapa 2: Limpieza y transformación de datos
def limpieza_transformacion(ruta_csv):
    run_id = str(uuid.uuid4())  # Generar un ID único para esta ejecución
    logging.info(f'RUN_ID: {run_id} - Iniciando limpieza y transformación de datos...')

    try:
        df = pd.read_csv(ruta_csv)

        # Anonimización de la columna 'customerID'
        df['customerID'] = df['customerID'].apply(encryptar_customerID)

        # Corrección de tipos de datos y manejo de valores faltantes en 'TotalCharges'
        df['TotalCharges'] = df['TotalCharges'].replace(r'^\s*$', np.nan, regex=True)
        df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')

        # Corrección de tipo de dato en 'SeniorCitizen' de numérico a categórico
        df['SeniorCitizen'] = df['SeniorCitizen'].replace({0: 'No', 1: 'Yes'})

        if df.empty:
            logging.warning(f'RUN_ID: {run_id} - ALERTA: El DataSet no contiene datos.')
        else:
            logging.info(f'RUN_ID: {run_id} - Limpieza y transformación completada con éxito.')
        return df
    except FileNotFoundError:
        logging.error(f'RUN_ID: {run_id} - Error no se encontró el archivo: {ruta_csv}')
    except Exception as e:
        logging.error(f'RUN_ID: {run_id} - Error crítico: {str(e)}')

if __name__ == "__main__":
    df_limpio = limpieza_transformacion(ruta_csv)
    if df_limpio is not None:
        df_limpio.to_csv('Data/Processed/Processing/02_Limpieza_Transformacion.csv', index=False)
        print("Datos limpios guardados en 'Data/Processed/Processing/02_Limpieza_Transformacion.csv'")