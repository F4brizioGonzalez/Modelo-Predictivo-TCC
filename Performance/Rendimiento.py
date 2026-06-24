import time
import os
import sys
import psutil
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


# --- CONFIGURACIÓN DEL LOGGER DE RENDIMIENTO ---
RUTA_REPORTE = 'Reports/Performance/Reporte_Rendimiento.log'
os.makedirs(os.path.dirname(RUTA_REPORTE), exist_ok=True)

# Se crea un logger específico para no interferir con el del pipeline principal
logger_perf = logging.getLogger("PerformanceMonitor")
logger_perf.setLevel(logging.INFO)

# Evitamos que duplique mensajes en la consola si el pipeline principal ya tiene un StreamHandler
logger_perf.propagate = False 

# Handler para escribir en el archivo de reporte (modo 'w' para sobrescribir en cada corrida, o 'a' para acumular)
file_handler = logging.FileHandler(RUTA_REPORTE, mode='w', encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger_perf.addHandler(file_handler)

# Lista que acumula el historial de métricas para cada etapa del pipeline
historial_Rendimiento = []

class PerformanceMonitor:
    def __init__(self, etapa_nombre):
        self.etapa_nombre = etapa_nombre
        self.process = psutil.Process(os.getpid())
        
    def __enter__(self):
        # Registra métricas al iniciar la etapa
        self.start_time = time.time()
        # psutil necesita una primera llamada para establecer el punto de partida del CPU
        self.process.cpu_percent(interval=None) 
        self.start_memory = self.process.memory_info().rss / (1024 * 1024) # Convierte a MB
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Registra métricas al finalizar la etapa
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss / (1024 * 1024)
        
        # Calcula diferencias e indicadores clave
        tiempo_total = self.end_time - self.start_time
        consumo_cpu = self.process.cpu_percent(interval=None)
        uso_memoria_final = self.end_memory
        
        # Captura errores si la etapa falla
        hubo_error = "No" if exc_type is None else f"Sí ({exc_type.__name__})"

        # Escribir en el log de rendimiento el resultado de la etapa de forma estructurada
        logger_perf.info(f"=== Resultados de: {self.etapa_nombre} ===")
        logger_perf.info(f" -> Tiempo de ejecución: {tiempo_total:.4f} segundos")
        logger_perf.info(f" -> Consumo de CPU: {consumo_cpu}%")
        logger_perf.info(f" -> Memoria RAM utilizada: {uso_memoria_final:.2f} MB")
        logger_perf.info(f" -> Errores detectados: {hubo_error}\n")

        # Guarda en el historial para análisis posterior
        historial_Rendimiento.append({
            "Etapa": self.etapa_nombre,
            "Tiempo": tiempo_total,
            "CPU": consumo_cpu,
            "RAM": uso_memoria_final,
            "Error": hubo_error
        })
        return False
    
def graficar_rendimiento_pipeline(historial):
    if not historial:
        return
        
    # Convierte el historial a un DataFrame de Pandas
    df = pd.DataFrame(historial)

    # Configuración Directorio
    carpeta_salida = "Reports/Figures/Performance"
    os.makedirs(carpeta_salida, exist_ok=True)
    
    # Configura el estilo visual con Seaborn
    sns.set_theme(style="whitegrid")     
    
    # 1. Gráfico de Tiempo de Ejecución
    fig, ax = plt.subplots(figsize=(8, 5))
    df_time = df.sort_values(by="Tiempo", ascending=True)
    sns.barplot(x="Tiempo", y="Etapa", data=df_time, ax=ax, palette="Blues_r", hue="Etapa", legend=False)
    ax.set_title("Tiempo de Ejecución por Etapa", fontsize=12, fontweight="bold")
    ax.set_xlabel("Segundos")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(f"{carpeta_salida}/rendimiento_tiempo.png", dpi=300)
    plt.close
    
    # 2. Gráfico de Consumo de CPU
    fig, ax = plt.subplots(figsize=(8, 5))
    df_cpu = df.sort_values(by="CPU", ascending=True)
    sns.barplot(x="CPU", y="Etapa", data=df_cpu, ax=ax, palette="Oranges_r", hue="Etapa", legend=False)
    ax.set_title("Consumo de CPU por Etapa", fontsize=12, fontweight="bold")
    ax.set_xlabel("Porcentaje de CPU (%)")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(f"{carpeta_salida}/rendimiento_cpu.png", dpi=300)
    plt.close
    
    # 3. Gráfico de Uso de Memoria RAM
    fig, ax = plt.subplots(figsize=(8, 5))
    df_ram = df.sort_values(by="RAM", ascending=True)
    sns.barplot(x="RAM", y="Etapa", data=df_ram, ax=ax, palette="Greens_r", hue="Etapa", legend=False)
    ax.set_title("Uso de Memoria RAM por Etapa", fontsize=12, fontweight="bold")
    ax.set_xlabel("Memoria RAM (MB)")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(f"{carpeta_salida}/rendimiento_ram.png", dpi=300)
    plt.close
    

def generar_reporte_final():
    if not historial_Rendimiento:
        logger_perf.warning("No hay métricas registradas para analizar.")
        return

    # 1. Calcula métricas globales del pipeline completo
    total_tiempo = sum(p["Tiempo"] for p in historial_Rendimiento)
    promedio_cpu = sum(p["CPU"] for p in historial_Rendimiento) / len(historial_Rendimiento)
    max_ram = max(p["RAM"] for p in historial_Rendimiento)

    errores_lista = [p["Error"] for p in historial_Rendimiento if p["Error"] != "No"]
    errores_detectados = "No" if not errores_lista else f"Sí ({', '.join(errores_lista)})"

    # 2. Identifica Cuellos de Botella (Máximos absolutos)
    etapa_mas_lenta = max(historial_Rendimiento, key=lambda x: x["Tiempo"])
    etapa_mas_cpu = max(historial_Rendimiento, key=lambda x: x["CPU"])
    etapa_mas_ram = max(historial_Rendimiento, key=lambda x: x["RAM"])

    # 3. Escribe el Reporte Final en el archivo de Logs
    logger_perf.info("================================================================")
    logger_perf.info("=== REPORTE DE RENDIMIENTO DEL PIPELINE COMPLETO ===")
    logger_perf.info("================================================================")
    logger_perf.info(f"Tiempo total de ejecución  : {total_tiempo:.4f} segundos")
    logger_perf.info(f"Consumo de CPU Promedio    : {promedio_cpu:.1f}%")
    logger_perf.info(f"Máxima memoria RAM usada   : {max_ram:.2f} MB")
    logger_perf.info(f"Errores detectados en flujo: {errores_detectados}")
    logger_perf.info("-" * 64)
    
    # Conclusiones del Pipeline (automatizadas)
    logger_perf.info("CUELLO DE BOTELLA POR TIEMPO:")
    logger_perf.info(f" -> [{etapa_mas_lenta['Etapa']}] con {etapa_mas_lenta['Tiempo']:.4f} segundos.")
    logger_perf.info("-" * 64)
    
    logger_perf.info("MAYOR CARGA DE RECURSOS:")
    logger_perf.info(f" -> CPU: [{etapa_mas_cpu['Etapa']}] alcanzando un {etapa_mas_cpu['CPU']}%")
    logger_perf.info(f" -> RAM: [{etapa_mas_ram['Etapa']}] alcanzando {etapa_mas_ram['RAM']:.2f} MB")
    logger_perf.info("================================================================")
    
    if errores_lista:
        etapas_con_error = [p["Etapa"] for p in historial_Rendimiento if p["Error"] != "No"]
        logger_perf.error(f"Fallas frecuentes detectadas en: {', '.join(etapas_con_error)}")
    
    graficar_rendimiento_pipeline(historial_Rendimiento)

