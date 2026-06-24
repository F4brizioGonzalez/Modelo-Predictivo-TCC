import pandas as pd
import joblib

ruta_archivo = 'Data/Processed/Validation/03_Validacion.csv'

# 1. Carga el modelo guardado previamente
try:
    model = joblib.load('Reports/ModelPredictive/modelo_churn.pkl')
    print("Modelo 'modelo_churn.pkl' cargado correctamente.")
except FileNotFoundError:
    print("Error: No se encontró el archivo del modelo. Debes ejecutar primero 'Entrenamiento.py'.")
    exit()

# 2. Carga los nuevos datos de los clientes actuales
print("Cargando nuevos datos para predecir...")
nuevos_clientes = pd.read_csv(ruta_archivo) 

# Limpieza rápida requerida por el modelo
nuevos_clientes['TotalCharges'] = nuevos_clientes['TotalCharges'].fillna(0)

# 3. Realiza las predicciones de probabilidad
# predict_proba nos devuelve dos columnas: [prob_quedarse, prob_irse].
probabilidades_churn = model.predict_proba(nuevos_clientes.drop(columns=['customerID', 'Churn'], errors='ignore'))[:, 1]

# 4. Añadir los resultados al DataFrame original para guardarlo de manera clara
nuevos_clientes['Probabilidad_Abandono %'] = (probabilidades_churn * 100).round(1)
nuevos_clientes['Prediccion_Final'] = nuevos_clientes['Probabilidad_Abandono %'].apply(lambda x: 'Alerta: Riesgo Alto' if x >= 50 else 'Estable')

# 5. Ordena a los clientes de mayor a menor riesgo
clientes_en_riesgo = nuevos_clientes.sort_values(by='Probabilidad_Abandono %', ascending=False)

# 6. Guarda el reporte en un nuevo archivo CSV 
columnas_reporte = ['customerID', 'Contract', 'MonthlyCharges', 'Probabilidad_Abandono %', 'Prediccion_Final']
clientes_en_riesgo[columnas_reporte].to_csv('Reports/ModelPredictive/reporte_riesgo_churn.csv', index=False)

print("\n¡Predicciones listas!")
print("Se ha generado el archivo 'reporte_riesgo_churn.csv' con los clientes ordenados por nivel de riesgo.")
print(clientes_en_riesgo[columnas_reporte].head(10))
