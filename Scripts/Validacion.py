import pandas as pd
import pandera.pandas as pa  
from pandera.pandas import Column, Check, DataFrameSchema
import logging
import os


# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Etapa 3 - Validación]: %(message)s',
    handlers=[
        logging.FileHandler("Data/Logs/03_Validacion.log", mode='w', encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# 1. DEFINICIÓN DEL ESQUEMA OPERACIONAL (Estructural y Semántico)
telco_schema = DataFrameSchema(
    columns={
        "customerID": Column(pa.String, unique=True, nullable=False),
        "gender": Column(pa.String, Check.isin(["Female", "Male"])),
        "SeniorCitizen": Column(pa.String, Check.isin(["No", "Yes"])),
        "Partner": Column(pa.String, Check.isin(["Yes", "No"])),
        "Dependents": Column(pa.String, Check.isin(["No", "Yes"])),
        "tenure": Column(pa.Int64, Check.ge(0)),
        "PhoneService": Column(pa.String, Check.isin(["No", "Yes"])),
        "MultipleLines": Column(pa.String, Check.isin(["No phone service", "No", "Yes"])),
        "InternetService": Column(pa.String, Check.isin(["DSL", "Fiber optic", "No"])),
        "OnlineSecurity": Column(pa.String, Check.isin(["No", "Yes", "No internet service"])),
        "OnlineBackup": Column(pa.String, Check.isin(["Yes", "No", "No internet service"])),
        "DeviceProtection": Column(pa.String, Check.isin(["No", "Yes", "No internet service"])),
        "TechSupport": Column(pa.String, Check.isin(["No", "Yes", "No internet service"])),
        "StreamingTV": Column(pa.String, Check.isin(["No", "Yes", "No internet service"])),
        "StreamingMovies": Column(pa.String, Check.isin(["No", "Yes", "No internet service"])),
        "Contract": Column(pa.String, Check.isin(["Month-to-month", "One year", "Two year"])),
        "PaperlessBilling": Column(pa.String, Check.isin(["Yes", "No"])),
        "PaymentMethod": Column(pa.String, Check.isin([
            "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
        ])),
        "MonthlyCharges": Column(pa.Float64, Check.ge(0)),
        "TotalCharges": Column(pa.Float64, Check.ge(0), nullable=True),
        "Churn": Column(pa.String, Check.isin(["No", "Yes"]))
    },
    # Validación Semántica Cruzada: Regla de negocio compleja
    checks=Check(
        lambda df: df[df["tenure"] == 0]["TotalCharges"].isna().all() or 
                  (df[df["tenure"] == 0]["TotalCharges"] == 0).all(),
        name="consistencia_clientes_nuevos",
        error="Inconsistencia lógica: Existen clientes con tenure=0 que registran cargos totales activos."
    ),
    strict=True,  
    ordered=True  
)

def validacion_datos(file_path: str):
    """
    Carga el dataset y ejecuta la validación vectorizada mediante Pandera
    """
    try:
        df = pd.read_csv(file_path)
        logging.info(f"Dataset cargado para inspección automatizada. Dimensiones: {df.shape}")
        
        # Validación con lazy=True recopila todos los errores antes de fallar
        validated_df = telco_schema.validate(df, lazy=True)
        
        logging.info("¡COMPUERTA DE CALIDAD SUPERADA [PASSED]! El dataset cumple con todas las especificaciones.")
        return True, validated_df

    except pa.errors.SchemaError as err:  # Corregido: Excepción correcta en Pandera
        logging.error("¡COMPUERTA DE CALIDAD FALLIDA [FAILED]! Se encontraron anomalías en el dataset.")
        
        failure_report = err.failure_cases
        print("\n" + "="*70)
        print("REPORTE AUTOMÁTICO DE ANOMALÍAS DETECTADAS")
        print("="*70)
        # Se verifica que existan las columnas en el reporte de fallas antes de imprimirlas
        cols_to_print = [c for c in ['column', 'check', 'failure_case', 'index'] if c in failure_report.columns]
        print(failure_report[cols_to_print].to_string(index=False))
        print("="*70 + "\n")
        
        return False, None

if __name__ == "__main__":
    csv_input = "Data/Processed/Processing/02_Limpieza_Transformacion.csv"
    os.makedirs(os.path.dirname(csv_input), exist_ok=True)
    
    # Corregido: Llamada real a la función de validación
    success, clean_df = validacion_datos(csv_input)
    
    if success and clean_df is not None:
        output_path = 'Data/Processed/Validation/03_Validacion.csv'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        clean_df.to_csv(output_path, index=False)
        logging.info(f"Datos validados exitosamente guardados en '{output_path}'")
    else:
        logging.error("El pipeline se ha detenido. Los datos no se guardaron debido a fallas de calidad.")
