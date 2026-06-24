import logging
import os
import sys

# 1. Obtiene la ruta de la carpeta 'scripts'
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
# 2. Sube un nivel para encontrar la raíz real del proyecto
RAIZ_PROYECTO = os.path.dirname(SCRIPTS_DIR)
# 3. Registra la raíz en el sistema de búsqueda de Python
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)
try:
    from Performance.Rendimiento import PerformanceMonitor, generar_reporte_final
except ModuleNotFoundError:
    from Performance.Rendimiento import PerformanceMonitor, generar_reporte_final

# Configuración del Logger Principal para la Orquestación
LOG_PIPELINE = 'Data/Logs/00_Pipeline_Principal.log'
os.makedirs("Data/Logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [PIPELINE]: %(message)s',
    handlers=[
        logging.FileHandler(LOG_PIPELINE, mode='w', encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

def ejecutar_pipeline():
    logging.info("INICIANDO PIPELINE AUTOMATIZADO DE DATAOPS (TELCO CHURN)")

    # ETAPA 1: Ingesta de Datos

    logging.info("-" * 70)
    logging.info("[ETAPA 1] Iniciando módulo de Ingesta...")
    try:
        with PerformanceMonitor("ETAPA 1: Ingesta de Datos"):
            from Ingesta import ingesta_datos, ruta_csv as ruta_raw
            
            df_raw = ingesta_datos(ruta_raw)
            if df_raw is None or df_raw.empty:
                raise ValueError("La ingesta no devolvió datos válidos. Abortando pipeline.")
            
            # Guardar estado intermedio
            ruta_ingesta_out = 'Data/Processed/Ingesta/01_Extraccion_Datos.csv'
            os.makedirs(os.path.dirname(ruta_ingesta_out), exist_ok=True)
            df_raw.to_csv(ruta_ingesta_out, index=False)
            logging.info(f"[ETAPA 1 COMPLETA] Datos ingestados guardados en: {ruta_ingesta_out}")
        
    except Exception as e:
        logging.critical(f"FALLO CRÍTICO EN ETAPA 1: {e}")
        sys.exit(1)

    # ETAPA 2: Limpieza y Transformación

    logging.info("-" * 70)
    logging.info("[ETAPA 2] Iniciando módulo de Limpieza y Transformación...")
    try:
        with PerformanceMonitor("ETAPA 2: Limpieza y Transformación"):
            from LimpiezaTransformacion import limpieza_transformacion
            
            df_limpio = limpieza_transformacion(ruta_ingesta_out)
            if df_limpio is None or df_limpio.empty:
                raise ValueError("La transformación devolvió un DataFrame vacío o nulo. Abortando pipeline.")
            
            # Guardar estado intermedio
            ruta_limpieza_out = 'Data/Processed/Processing/02_Limpieza_Transformacion.csv'
            os.makedirs(os.path.dirname(ruta_limpieza_out), exist_ok=True)
            df_limpio.to_csv(ruta_limpieza_out, index=False)
            logging.info(f"[ETAPA 2 COMPLETA] Datos limpios guardados en: {ruta_limpieza_out}")
        
    except Exception as e:
        logging.critical(f"FALLO CRÍTICO EN ETAPA 2: {e}")
        sys.exit(1)

    # ETAPA 3: Validación con Pandera (Compuerta de Calidad)

    logging.info("-" * 70)
    logging.info("[ETAPA 3] Iniciando Compuerta de Calidad (Validación)...")
    try:
        with PerformanceMonitor("ETAPA 3: Validación de Datos"):
            from Validacion import validacion_datos
            
            success, df_validado = validacion_datos(ruta_limpieza_out)
            
            if not success or df_validado is None:
                raise AssertionError("El dataset NO superó las reglas de calidad de Pandera. Deteniendo el flujo.")
            
            # Guardar estado validado
            ruta_validacion_out = 'Data/Processed/Validation/03_Validacion.csv'
            os.makedirs(os.path.dirname(ruta_validacion_out), exist_ok=True)
            df_validado.to_csv(ruta_validacion_out, index=False)
            logging.info(f"[ETAPA 3 COMPLETA] Compuerta superada. Datos validados en: {ruta_validacion_out}")
        
    except Exception as e:
        logging.critical(f"FALLO CRÍTICO EN ETAPA 3: {e}")
        sys.exit(1)


    # ETAPA 4: Carga y Persistencia (SQLite)

    logging.info("-" * 70)
    logging.info("[ETAPA 4] Iniciando módulo de Carga a Base de Datos...")
    try:
        with PerformanceMonitor("ETAPA 4: Carga y Persistencia en SQLite"):
            from CargaDeDatos import cargar_datos
            
            # La función de carga lee internamente desde 'Data/Processed/Validation/03_Validacion.csv'
            cargar_datos()
            logging.info("[ETAPA 4 COMPLETA] Persistencia en SQLite finalizada exitosamente.")
        
    except Exception as e:
        logging.critical(f"FALLO CRÍTICO EN ETAPA 4: {e}")
        sys.exit(1)
    
    # ETAPA 5: Entrenamiento del Modelo 
    print("-" * 70)
    logging.info("[ETAPA 5] Iniciando módulo de Entrenamiento del Modelo...")
    try:
        with PerformanceMonitor("ETAPA 5 - Entrenamiento del Modelo"):
            import ModeloPredictivo.Entrenamiento
            logging.info("[ETAPA 5 COMPLETA] Entrenamiento del modelo finalizado exitosamente.")
        
    except Exception as e:
        logging.critical(f"FALLO CRÍTICO EN ETAPA 5: {e}")
        sys.exit(1)

    # ETAPA 6: Modelo Predictivo y Evaluación
    print("-" * 70)
    logging.info("[ETAPA 6] Iniciando Modelo Predictivo y Evaluación...")
    try:
        with PerformanceMonitor("ETAPA 6 - Evaluación del Modelo"):
            import ModeloPredictivo.Predictivo
            logging.info("[ETAPA 6 COMPLETA] Evaluación del modelo finalizada exitosamente.")
        
    except Exception as e:
        logging.critical(f"FALLO CRÍTICO EN ETAPA 6: {e}")
        sys.exit(1)
    
    print("-" * 70)
    logging.info("[ETAPA 7] Iniciando Generación de Gráficos...")
    try:
        import ModeloPredictivo.Visualizaciones
        logging.info("[ETAPA 7 COMPLETA] Gráficos 'matriz_confusion.png' y 'curva_roc.png' generados en Reports/Figures/Modelo.") 
    except Exception as e:
        logging.critical(f"FALLO CRÍTICO EN ETAPA 7: {e}")
        sys.exit(1)

    logging.info("-" * 70)
    logging.info("PIPELINE EJECUTADO EXITOSAMENTE")
    logging.info("-" * 70)

    # Generar reporte final de rendimiento
    generar_reporte_final()
    logging.info("REPORTE FINAL DE RENDIMIENTO GENERADO EXITOSAMENTE EN 'Data/Reports/Reporte_Rendimiento.log'")

    

if __name__ == "__main__":
    ejecutar_pipeline()