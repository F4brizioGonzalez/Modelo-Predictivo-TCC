import pandas as pd
import numpy as np
import logging
import uuid


# Definir la ruta del archivo CSV
ruta_csv = "Data/Raw/02_Base_WA_Fn-UseC_-Telco-Customer-Churn.csv"

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Etapa 1 - Ingesta]: %(message)s',
    handlers=[
        logging.FileHandler("Data/Logs/01_Ingesta_Datos.log"),
        logging.StreamHandler()
    ]
)
# Etapa 1: Ingesta de datos
def ingesta_datos(ruta_csv):
    run_id = str(uuid.uuid4())  # Generar un ID único para esta ejecución
    logging.info("Iniciando Pipeline de Datos ....")

    try:
        df = pd.read_csv(ruta_csv)
        num_filas = len(df)
        columnas = len(df.columns)
        print("Ingesta de datos completada exitosamente.")

        logging.info(f'RUN_ID: {run_id} - Ingesta exitosa. Número de filas: {num_filas}, Columnas: {columnas}')

        if df.empty:
            logging.warning(f'RUN_ID: {run_id} - ALERTA: El DataSet no contiene datos.')
        else:
            logging.info(f'RUN_ID: {run_id} - Ingesta completada con éxito.')
        return df
    except FileNotFoundError:
        logging.error(f'RUN_ID: {run_id} - Error no se encontró el archivo: {ruta_csv}')
    except Exception as e:
        logging.error(f'RUN_ID: {run_id} - Error crítico: {str(e)}')


if __name__ == "__main__":
    df = ingesta_datos(ruta_csv)
    if df is not None:
        df_final = df
        df_final.to_csv('Data/Processed/Ingesta/01_Extraccion_Datos.csv', index=False)
        print("Datos Ingestados Exitosamente en: Data/Processed/Ingesta/01_Extraccion_Datos.csv")