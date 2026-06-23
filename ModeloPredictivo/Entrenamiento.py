import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)


ruta_archivo = 'Data/Processed/Validation/03_Validacion.csv'

print("Cargando y preparando los datos...")
# 1. Cargar el dataset limpio y validado
df = pd.read_csv(ruta_archivo)

# 2. Tratamiento de nulos específicos (Nuevos clientes con tenure = 0)
df['TotalCharges'] = df['TotalCharges'].fillna(0)

# 3. Separar características (X) y Variable Objetivo (y)
X = df.drop(columns=['customerID', 'Churn'])
y = df['Churn'].apply(lambda x: 1 if x == 'Yes' else 0)

# 4. Identificar columnas por tipo de dato
categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
numerical_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

# 5. Crear el Preprocesador (Escala números y codifica categorías automáticamente)
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols)
    ])

# 6. Definir el Pipeline completo junto con la Regresión Logística
model_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', LogisticRegression(max_iter=1000, random_state=42))
])

# 7. Dividir en set de entrenamiento y validación (80% / 20%)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Entrenando el modelo predictivo...")
model_pipeline.fit(X_train, y_train)

# 8. Evaluar el rendimiento del modelo en el set de prueba (Capacidad de discriminación)
y_pred = model_pipeline.predict(X_test)
y_proba = model_pipeline.predict_proba(X_test)[:, 1]

# Evaluación detallada del modelo
RendimientoModelo = {
    'Accuracy': accuracy_score(y_test, y_pred),
    'Precision': precision_score(y_test, y_pred),
    'Recall': recall_score(y_test, y_pred),
    'F1-Score': f1_score(y_test, y_pred),
}


# Comparación de modelos
modelos = {
    'Regresión Logística': LogisticRegression(max_iter=1000),
    'Random Forest': RandomForestClassifier(),
    'Gradient Boosting': GradientBoostingClassifier()
}

resultados_comparacion = []

for nombre, modelo in modelos.items():

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', modelo)
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    resultados_comparacion.append({
        "Modelo": nombre,
        "Accuracy": round(accuracy, 4),
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1": round(f1, 4),
        "AUC": round(auc, 4),
    })


pd.DataFrame(resultados_comparacion).to_csv('Reports/ModelPredictive/Resultados_Comparacion_Modelos.csv', index=False)

print("\n================ EVALUACIÓN DEL MODELO ================")
for metric, value in RendimientoModelo.items():
    print(f"{metric}: {value:.4f}")

print(f"Métrica AUC-ROC: {roc_auc_score(y_test, y_proba):.4f}\n")
print("Resultados de comparación entre modelos:")
print(pd.DataFrame(resultados_comparacion))
print("=======================================================\n")

# 9. Guardar el pipeline completo (incluye el preprocesamiento y el modelo)
joblib.dump(model_pipeline, 'Reports/ModelPredictive/modelo_churn.pkl')
print("¡Éxito! El modelo ha sido entrenado y guardado como 'modelo_churn.pkl'")

