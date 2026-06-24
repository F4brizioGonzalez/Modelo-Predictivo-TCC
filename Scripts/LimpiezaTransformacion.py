import pandas as pd
import numpy as np
import logging
import uuid
import hashlib
import os

# Definir la ruta del archivo CSV 
ruta_csv = "Data/Processed/Ingesta/01_Extraccion_Datos.csv"
os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)

ruta_salida = "Data/Processed/Limpieza_Transformacion/02_Datos_Limpios.csv"
os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Etapa 2 - Limpieza y Transformación]: %(message)s',
    handlers=[
        logging.FileHandler("Data/Logs/01_Limpieza_Transformacion.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Fase de seguridad para la gestión de datos sensibles
# Aplicando anonimización según Ley 19.628 (Sha-256) + Salting
def encryptar_customerID(customerID, salt="Salt_Unico"):
    if pd.isna(customerID):
        return np.nan
    texto_a_encriptar = f"{salt}{str(customerID)}"
    return hashlib.sha256(texto_a_encriptar.encode()).hexdigest()[:8]

# NUEVA FUNCIÓN: Modulo de procesamiento por bloque
def procesar_bloque(df, run_id):

    if df is None or df.empty:
        return df

    # 1. LIMPIEZA GENÉRICA: Eliminar columnas 100% vacías
    columnas_antes = df.shape[1]
    df = df.dropna(how='all', axis=1)
    columnas_despues = df.shape[1]
    
    if columnas_antes != columnas_despues:
        logging.info(f'RUN_ID: {run_id} - LIMPIEZA: Se eliminaron {columnas_antes - columnas_despues} columna(s) completamente vacía(s).')

    # 2. LIMPIEZA ESPECÍFICA: Anonimización de la columna 'customerID'
    if 'customerID' in df.columns:
        df['customerID'] = df['customerID'].apply(encryptar_customerID)

    # 3. LIMPIEZA ESPECÍFICA: Corrección de tipos de datos en 'TotalCharges'
    if 'TotalCharges' in df.columns:
        df['TotalCharges'] = df['TotalCharges'].replace(r'^\s*$', np.nan, regex=True)
        df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')

    # 4. LIMPIEZA ESPECÍFICA: Corrección de tipo de dato en 'SeniorCitizen'
    if 'SeniorCitizen' in df.columns:
        df['SeniorCitizen'] = df['SeniorCitizen'].replace({0: 'No', 1: 'Yes'})

    return df

# Etapa 2: Limpieza y transformación de datos
def limpieza_transformacion(ruta_csv, chunk_size=None):
    run_id = str(uuid.uuid4())[:12]  # Generar un ID único para esta ejecución
    logging.info(f'RUN_ID: {run_id} - Iniciando limpieza y transformación de datos...')

    try:
        # LÓGICA DE ESCALABILIDAD: definimos chunk_size para procesar el CSV en bloques si es necesario
        if chunk_size:
            logging.info(f'RUN_ID: {run_id} - Modo Escalable Activo: Procesando en bloques de {chunk_size} filas.')
            chunks = pd.read_csv(ruta_csv, chunksize=chunk_size)
            df_final = pd.concat([procesar_bloque(chunk, run_id) for chunk in chunks], ignore_index=True)
        else:
            df = pd.read_csv(ruta_csv)
            df_final = procesar_bloque(df, run_id)

        # Validar si el dataframe final quedó vacío tras las limpiezas
        if df_final is None or df_final.empty:
            logging.warning(f'RUN_ID: {run_id} - ALERTA: El DataSet final no contiene datos.')
        else:
            logging.info(f'RUN_ID: {run_id} - Limpieza y transformación completada con éxito. Columnas finales: {len(df_final.columns)}')
            
        return df_final

    except FileNotFoundError:
        logging.error(f'RUN_ID: {run_id} - Error: No se encontró el archivo en la ruta: {ruta_csv}')
    except Exception as e:
        logging.error(f'RUN_ID: {run_id} - Error crítico en el pipeline: {str(e)}')

if __name__ == "__main__":
    # ESCALABILIDAD: Cambiar 'chunk_size=None' por un entero si el archivo supera la memoria RAM.
    df_limpio = limpieza_transformacion(ruta_csv, chunk_size=None)
    
    if df_limpio is not None:
        # Asegurar que el directorio de salida exista
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        
        # CIFRADO EN TRÁNSITO / ALMACENAMIENTO SEGURO
        df_limpio.to_csv(ruta_salida, index=False)
        try:
            os.chmod(ruta_salida, 0o600)
            logging.info(f"SEGURIDAD: Permisos restrictivos aplicados a {ruta_salida}")
        except OSError:
            pass
            
        logging.info(f"Datos limpios guardados exitosamente en '{ruta_salida}'")