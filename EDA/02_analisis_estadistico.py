import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# Rutas del ecosistema
ruta_entrada = "Data/Processed/Ingesta/01_Extraccion_Datos.csv"
carpeta_graficos = "Reports/EDA"
os.makedirs(carpeta_graficos, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [EDA - Análisis Estadístico]: %(message)s',
    handlers=[
        logging.FileHandler("Data/Logs/03_Analisis_Estadistico.log"),
        logging.StreamHandler()
    ]
)

def ejecutar_analisis_estadistico(ruta_csv):
    logging.info("Iniciando análisis univariado, bivariado y matricial...")
    try:
        df = pd.read_csv(ruta_csv)
        
        # Asegurar limpieza básica de TotalCharges para visualización correcta
        if 'TotalCharges' in df.columns:
            df['TotalCharges'] = pd.to_numeric(df['TotalCharges'].astype(str).str.strip(), errors='coerce').fillna(0.0)

        # 1. ANÁLISIS UNIVARIADO: MONTHLYCHARGES
        logging.info("Generando gráfico univariado (MonthlyCharges)...")
        plt.figure(figsize=(8, 4))
        sns.histplot(df['MonthlyCharges'], kde=True, color='skyblue', bins=30)
        plt.title('Análisis Univariado: Distribución de Cargos Mensuales', fontsize=12, fontweight='bold')
        plt.xlabel('Cargos Mensuales')
        plt.ylabel('Frecuencia (Cantidad de Clientes)')
        plt.tight_layout()
        plt.savefig(f"{carpeta_graficos}/01_univariado_distribucion.png", dpi=300)
        plt.close()

        # ANÁLISIS UNIVARIADO: TERNURE
        logging.info("Generando gráfico univariado (tenure)...")
        plt.figure(figsize=(8, 4))
        sns.histplot(df['tenure'], kde=True, color='skyblue', bins=30)
        plt.title('Análisis Univariado: Distribución de Permanencia (Tenure)', fontsize=12, fontweight='bold')
        plt.xlabel('Meses de Antigüedad')
        plt.ylabel('Frecuencia (Cantidad de Clientes)')
        plt.tight_layout()
        plt.savefig(f"{carpeta_graficos}/01_univariado_ternure.png", dpi=300)
        plt.close()

        # ANÁLISIS UNIVARIADO: Contract
        logging.info("Generando gráfico univariado (contract)...")
        plt.figure(figsize=(8, 4))
        sns.histplot(df['Contract'], kde=True, color='skyblue', bins=30)
        plt.title('Análisis Univariado: Distribución del Tipo de Contrato', fontsize=12, fontweight='bold')
        plt.xlabel('Modalidad Contractual')
        plt.ylabel('Frecuencia (Cantidad de Clientes)')
        plt.tight_layout()
        plt.savefig(f"{carpeta_graficos}/01_univariado_Contract.png", dpi=300)
        plt.close()

        # 2. ANÁLISIS BIVARIADO: Tipo de Contrato vs Churn
        logging.info("Generando gráfico bivariado (Contract vs Churn)...")
        if 'Contract' in df.columns and 'Churn' in df.columns:
            plt.figure(figsize=(8, 5))
            sns.countplot(x='Contract', hue='Churn', data=df, palette='Set2')
            plt.title('Análisis Bivariado: Impacto del Tipo de Contrato en el Churn', fontsize=12, fontweight='bold')
            plt.xlabel('Tipo de Contrato')
            plt.ylabel('Cantidad de Clientes')
            plt.legend(title='Fuga (Churn)')
            plt.tight_layout()
            plt.savefig(f"{carpeta_graficos}/02_bivariado_contrato_vs_churn.png", dpi=300)
            plt.close()

        # 2. ANÁLISIS BIVARIADO: Tenure vs Churn
        logging.info("Generando gráfico bivariado (tenure vs Churn)...")
        if 'tenure' in df.columns and 'Churn' in df.columns:
            plt.figure(figsize=(8, 5))
            sns.boxplot(x='Churn', y='tenure', data=df, palette='Set2')
            plt.title('Análisis Bivariado: Antigüedad de los Clientes según Estado de Fuga', fontsize=12, fontweight='bold')
            plt.xlabel('¿El cliente se fugó? (Churn)')
            plt.ylabel('Meses de Antigüedad (Tenure)')
            plt.tight_layout()
            plt.savefig(f"{carpeta_graficos}/02_bivariado_tenure_vs_churn.png", dpi=300)
            plt.close()


        # 3. MATRIZ DE CORRELACIÓN (Variables Numéricas Clave)
        logging.info("Calculando matriz de correlación matricial...")
        columnas_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(columnas_numericas) > 1:
            plt.figure(figsize=(8, 6))
            matriz_corr = df[columnas_numericas].corr()
            
            sns.heatmap(matriz_corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
            plt.title('Matriz de Correlación Lineal (Variables Numéricas)', fontsize=12, fontweight='bold')
            plt.tight_layout()
            plt.savefig(f"{carpeta_graficos}/03_matriz_correlacion.png", dpi=300)
            plt.close()
            logging.info("Matriz de correlación exportada con éxito.")
            
    except Exception as e:
        logging.error(f"Error crítico en el análisis estadístico: {str(e)}")

if __name__ == "__main__":
    ejecutar_analisis_estadistico(ruta_entrada)