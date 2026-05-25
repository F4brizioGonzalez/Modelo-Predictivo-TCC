import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
import joblib

ruta_archivo = 'Data/Processed/Validation/03_Validacion.csv'

print("Cargando y preparando los datos...")
# 1. Cargar el dataset limpio y validado
df = pd.read_csv(ruta_archivo)

# 2. Tratamiento de nulos específicos (Nuevos clientes con tenure = 0)
df['TotalCharges'] = df['TotalCharges'].fillna(0)

# 3. Separar características (X) y etiqueta objetivo (y)
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

print("\n================ EVALUACIÓN DEL MODELO ================")
print(classification_report(y_test, y_pred))
print(f"Métrica AUC-ROC: {roc_auc_score(y_test, y_proba):.4f}")
print("=======================================================\n")

# 9. Guardar el pipeline completo (incluye el preprocesamiento y el modelo)
joblib.dump(model_pipeline, 'ModelPredictive/modelo_churn.pkl')
print("¡Éxito! El modelo ha sido entrenado y guardado como 'modelo_churn.pkl'")