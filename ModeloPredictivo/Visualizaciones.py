import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_curve, roc_auc_score
import joblib

# 1. Configuración de estilos y rutas
sns.set_theme(style="whitegrid")
ruta_datos = 'Data/Processed/Validation/03_Validacion.csv'
ruta_modelo = 'Reports/ModelPredictive/modelo_churn.pkl'

print("Cargando modelo y datos necesarios...")

# Verifica si el modelo existe
if not os.path.exists(ruta_modelo):
    print(f"Error: No se encontró el modelo en '{ruta_modelo}'. Primero debes ejecutar el script de entrenamiento.")
    exit()

# Carga el modelo
model_pipeline = joblib.load(ruta_modelo)

# Carga y limpia el dataset como lo hace el entrenamiento
df = pd.read_csv(ruta_datos)
df['TotalCharges'] = df['TotalCharges'].fillna(0)

# 2. Replica la misma separación de datos del entrenamiento
X = df.drop(columns=['customerID', 'Churn'], errors='ignore')
y = df['Churn'].apply(lambda x: 1 if x == 'Yes' else 0)

# Se mantiene mismas configuraciones del archivo entrenamineto para mantener consistencias
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Calculando predicciones y probabilidades de prueba...")
y_pred = model_pipeline.predict(X_test)
y_proba = model_pipeline.predict_proba(X_test)[:, 1]

# GENERACIÓN DE GRÁFICOS
print("\nGenerando y guardando los gráficos...")

# Gráfico 1: Matriz de Confusión
fig2, ax2 = plt.subplots(figsize=(6, 5))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
            xticklabels=['No Churn', 'Churn'], yticklabels=['No Churn', 'Churn'], 
            ax=ax2, annot_kws={"size": 14})
ax2.set_title('Matriz de Confusión', fontsize=14, fontweight='bold', pad=15)
ax2.set_xlabel('Predicción del Modelo', fontsize=12)
ax2.set_ylabel('Clase Real (Terreno)', fontsize=12)
plt.tight_layout()
plt.savefig('Reports/Figures/Modelo/matriz_confusion.png', dpi=150)
plt.close()
print("- 'matriz_confusion.png' generado.")

# Gráfico 2: Curva ROC
fpr, tpr, thresholds = roc_curve(y_test, y_proba)
auc_val = roc_auc_score(y_test, y_proba)

fig3, ax3 = plt.subplots(figsize=(6, 5))
ax3.plot(fpr, tpr, color='darkorange', lw=2, label=f'Curva ROC (AUC = {auc_val:.4f})')
ax3.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
ax3.set_xlim([0.0, 1.0])
ax3.set_ylim([0.0, 1.05])
ax3.set_xlabel('Tasa de Falsos Positivos (1 - Especificidad)', fontsize=12)
ax3.set_ylabel('Tasa de Verdaderos Positivos (Sensibilidad)', fontsize=12)
ax3.set_title('Curva ROC del Modelo', fontsize=14, fontweight='bold', pad=15)
ax3.legend(loc="lower right", fontsize=11)
ax3.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('Reports/Figures/Modelo/curva_roc.png', dpi=150)
plt.close()
print("- 'curva_roc.png' generado.")

print("\n Los  archivos visuales han sido guardados en el directorio actual.")