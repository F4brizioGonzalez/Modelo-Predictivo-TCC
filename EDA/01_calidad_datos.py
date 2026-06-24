import os
import pandas as pd
import numpy as np
import logging

# Configuración de rutas 
ruta_entrada = "Data/Processed/Ingesta/01_Extraccion_Datos.csv"
carpeta_reportes = "Reports/EDA"
os.makedirs(carpeta_reportes, exist_ok=True)

# Configuración del Logging 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [EDA - Calidad de Datos]: %(message)s',
    handlers=[
        logging.FileHandler("Data/Logs/02_Calidad_Datos.log"),
        logging.StreamHandler()
    ]
)

def auditoria_calidad_datos(ruta_csv):
    logging.info("Iniciando auditoría de calidad de datos...")
    try:
        df = pd.read_csv(ruta_csv)
        total_filas = len(df)
        
        reporte_calidad = []
        
        for col in df.columns:
            nulos = df[col].isna().sum()
            pct_nulos = (nulos / total_filas) * 100
            tipo_dato = df[col].dtype
            
            if pd.api.types.is_numeric_dtype(df[col]):
                media = df[col].mean()
                moda = df[col].mode().iloc[0] if not df[col].mode().empty else np.nan
                p25 = df[col].quantile(0.25)
                p50 = df[col].quantile(0.50) 
                p75 = df[col].quantile(0.75)
            else:

                media, p25, p50, p75 = "N/A", "N/A", "N/A", "N/A"
                moda = df[col].mode().iloc[0] if not df[col].mode().empty else np.nan
            
            reporte_calidad.append({
                "Variable": col,
                "Tipo_Dato": str(tipo_dato),
                "Valores_Nulos": int(nulos),
                "Pct_Nulos": round(pct_nulos, 2),
                "Media": media if media == "N/A" else round(float(media), 4),
                "Moda": str(moda) if pd.notna(moda) else "N/A",
                "Percentil_25": p25 if p25 == "N/A" else round(float(p25), 4),
                "Percentil_50_Mediana": p50 if p50 == "N/A" else round(float(p50), 4),
                "Percentil_75": p75 if p75 == "N/A" else round(float(p75), 4)
            })
            
        df_reporte = pd.DataFrame(reporte_calidad)
        ruta_guardado = f"{carpeta_reportes}/Reporte_Calidad_Métricas.csv"
        df_reporte.to_csv(ruta_guardado, index=False)
        logging.info(f"Auditoría completada con éxito. Reporte métrico guardado en: {ruta_guardado}")
        
        logging.info("Aplicando reglas operacionales de imputación...")
        
        if 'TotalCharges' in df.columns:
            df['TotalCharges'] = pd.to_numeric(df['TotalCharges'].astype(str).str.strip(), errors='coerce')
            conteo_nulos_antes = df['TotalCharges'].isna().sum()
            
            df['TotalCharges'] = df['TotalCharges'].fillna(0.0)
            logging.info(f"Imputación aplicada en 'TotalCharges': {conteo_nulos_antes} valores nulos corregidos con 0.0.")
            
        return df

    except FileNotFoundError:
        logging.error(f"No se encontró el archivo de datos en la ruta: {ruta_csv}")
    except Exception as e:
        logging.error(f"Error crítico en la fase de calidad: {str(e)}")

if __name__ == "__main__":
    df_auditado = auditoria_calidad_datos(ruta_entrada)