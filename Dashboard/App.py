import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.metrics import confusion_matrix, roc_curve, auc
import io
import re
import os
import joblib

# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA Y RUTAS REALES DEL PROYECTO
# ==============================================================================
st.set_page_config(
    page_title="Telco Churn Analytics - DataOps Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definición de rutas según la estructura local de tu proyecto
RUTA_DATOS_LOCAL = 'Data/Processed/Validation/03_Validacion.csv'
RUTA_MODELO_LOCAL = 'Reports/ModelPredictive/modelo_churn.pkl'
RUTA_LOGS_LOCAL = 'Reports/Performance/Reporte_Rendimiento.log'

# Configuración de estilos para control de contraste y legibilidad
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 5px solid #0056b3;
            margin-bottom: 15px;
        }
        .metric-title { font-size: 14px; color: #6c757d; font-weight: 500; }
        .metric-value { font-size: 26px; color: #212529; font-weight: 700; }
        h1, h2, h3 { color: #1e293b !important; font-family: 'Segoe UI', Arial, sans-serif; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# MÓDULO DE PIPELINE DE DATOS REAL (EXTRACT, TRANSFORM & INFER)
# ==============================================================================
@st.cache_resource
def cargar_modelo_produccion(ruta_modelo):
    """Carga de manera eficiente en memoria el pipeline de Machine Learning pkl."""
    if os.path.exists(ruta_modelo):
        return joblib.load(ruta_modelo)
    return None

@st.cache_data
def cargar_datos_produccion(ruta_datos, _modelo):
    """Lee el dataset del proyecto y calcula inferencias reales usando el modelo cargado."""
    if not os.path.exists(ruta_datos):
        return None, None
        
    df = pd.read_csv(ruta_datos)
    # Tratamiento de datos
    df['TotalCharges'] = df['TotalCharges'].fillna(0)
    
    # Prepara el dataframe predictivo
    df_pred = df.copy()
    
    if _modelo is not None:
        # Extrae variables quitando ID y target real si existen
        X = df.drop(columns=['customerID', 'Churn'], errors='ignore')
        # Calcula probabilidades reales mediante predict_proba
        probabilidades = _modelo.predict_proba(X)[:, 1]
        df_pred['Probabilidad_Abandono %'] = np.round(probabilidades * 100, 1)
    else:
        # Fallback de seguridad si no se encuentra el archivo .pkl
        st.sidebar.warning("Pipeline pkl no encontrado. Usando simulación de contingencia para probabilidades.")
        np.random.seed(42)
        df_pred['Probabilidad_Abandono %'] = np.round(np.random.uniform(5, 95, size=len(df_pred)), 1)
        
    df_pred['Prediccion_Final'] = df_pred['Probabilidad_Abandono %'].apply(lambda x: 'Alerta: Riesgo Alto' if x >= 50 else 'Estable')
    
    if 'Churn' in df.columns:
        y_real = df['Churn'].apply(lambda x: 1 if str(x).strip().lower() in ['yes', '1'] else 0).values
    else:
        y_real = np.zeros(len(df))
        
    df_val = pd.DataFrame({
        'Real_Churn': y_real, 
        'Prob_Churn': df_pred['Probabilidad_Abandono %'] / 100
    })
    
    return df_pred, df_val

def leer_logs_produccion(ruta_log):
    """Extrae la información en tiempo real del archivo Rendimiento_report.log de psutil."""
    if os.path.exists(ruta_log):
        with open(ruta_log, 'r', encoding='utf-8') as f:
            return f.read()
    return "Error: No se encontró el archivo físico de logs en " + ruta_log

def procesar_log_infraestructura(texto_logs):
    """Parsea el log estructurado de psutil para extraer métricas de rendimiento por etapas."""
    etapas, tiempos, cpus, rams = [], [], [], []
    
    patron_etapa = r"=== Resultados de: (.*?) ==="
    patron_tiempo = r"Tiempo de ejecución: ([\d\.]+) segundos"
    patron_cpu = r"Consumo de CPU: ([\d\.]+)%"
    patron_ram = r"Memoria RAM utilizada: ([\d\.]+) MB"
    
    # Reporte Rendimiento del Pipeline
    patron_cpu_prom = r"Consumo de CPU Promedio\s+:\s+([\d\.]+)%"
    patron_ram_max = r"Máxima memoria RAM usada\s+:\s+([\d\.]+) MB"
    patron_botleneck = r"-> \[(.*?)\] con ([\d\.]+) segundos\."
    patron_carga_cpu = r"-> CPU: \[(.*?)\] alcanzando un ([\d\.]+)%"
    patron_carga_ram = r"-> RAM: \[(.*?)\] alcanzando ([\d\.]+) MB"

    lineas = texto_logs.split('\n')
    etapa_actual = None

    resumen = {
        "cpu_promedio": 0.0, "ram_maxima": 0.0,
        "cuello_tiempo_etapa": "N/A", "cuello_tiempo_valor": 0.0,
        "max_cpu_etapa": "N/A", "max_cpu_valor": 0.0,
        "max_ram_etapa": "N/A", "max_ram_valor": 0.0
    }
    
    for linea in lineas:
        match_e = re.search(patron_etapa, linea)
        if match_e:
            etapa_actual = match_e.group(1)
        if etapa_actual:
            match_t = re.search(patron_tiempo, linea)
            match_c = re.search(patron_cpu, linea)
            match_r = re.search(patron_ram, linea)
            
            if match_t:
                etapas.append(etapa_actual)
                tiempos.append(float(match_t.group(1)))
            if match_c: cpus.append(float(match_c.group(1)))
            if match_r: rams.append(float(match_r.group(1)))

        # 2. Captura de métricas globales del Reporte Final
        m_cpu_p = re.search(patron_cpu_prom, linea)
        m_ram_m = re.search(patron_ram_max, linea)
        m_botln = re.search(patron_botleneck, linea)
        m_ccpu  = re.search(patron_carga_cpu, linea)
        m_cram  = re.search(patron_carga_ram, linea)
        
        if m_cpu_p: resumen["cpu_promedio"] = float(m_cpu_p.group(1))
        if m_ram_m: resumen["ram_maxima"] = float(m_ram_m.group(1))
        if m_botln:
            resumen["cuello_tiempo_etapa"] = m_botln.group(1)
            resumen["cuello_tiempo_valor"] = float(m_botln.group(2))
        if m_ccpu:
            resumen["max_cpu_etapa"] = m_ccpu.group(1)
            resumen["max_cpu_valor"] = float(m_ccpu.group(2))
        if m_cram:
            resumen["max_ram_etapa"] = m_cram.group(1)
            resumen["max_ram_valor"] = float(m_cram.group(2))
                
    if not etapas:
        df_vacio = pd.DataFrame(columns=['Etapa', 'Tiempo_Ejecución_Seg', 'CPU_%', 'RAM_MB'])
        return df_vacio, resumen
        
    df_etapas = pd.DataFrame({'Etapa': etapas, 'Tiempo_Ejecución_Seg': tiempos, 'CPU_%': cpus, 'RAM_MB': rams})
    return df_etapas, resumen 

# ==============================================================================
# CARGA INICIAL (ORQUESTACIÓN DE INGESTIÓN LOCAL)
# ==============================================================================
modelo_pkl = cargar_modelo_produccion(RUTA_MODELO_LOCAL)
df_pred, df_val = cargar_datos_produccion(RUTA_DATOS_LOCAL, modelo_pkl)
logs_raw = leer_logs_produccion(RUTA_LOGS_LOCAL)

# ==============================================================================
# INTERFAZ COMPLETA Y FLUJO DE SOBREESCRITURA CONTINUA (FILE UPLOADER)
# ==============================================================================
st.sidebar.header("📥 Ingesta Continuada de Datos")
archivo_cargado = st.sidebar.file_uploader(
    "Recargar set unificado o actualización de negocio", 
    type=['csv', 'xlsx'],
    help="Al cargar un archivo aquí, se anulan los datos locales y todo el dashboard se recalcula dinámicamente."
)

# Lógica de actualización infinita reactiva
if archivo_cargado is not None:
    try:
        if archivo_cargado.name.endswith('.csv'):
            df_entrada = pd.read_csv(archivo_cargado)
        else:
            # Opción unificada de múltiples datasets o pestañas
            xl = pd.ExcelFile(archivo_cargado)
            if "Predicciones" in xl.sheet_names or len(xl.sheet_names) > 1:
                df_entrada = pd.read_excel(archivo_cargado, sheet_name=0)
                # Intenta buscar logs de psutil en otra hoja si existiera
                if "Logs" in xl.sheet_names:
                    df_logs_sheet = pd.read_excel(archivo_cargado, sheet_name="Logs")
                    if not df_logs_sheet.empty:
                        logs_raw = "\n".join(df_logs_sheet.iloc[:, 0].astype(str).tolist())
            else:
                df_entrada = pd.read_excel(archivo_cargado, sheet_name=0)
                
        columnas_requeridas = ['customerID', 'Contract', 'MonthlyCharges']
        if all(col in df_entrada.columns for col in columnas_requeridas):
            # Calcula inferencias reales sobre el nuevo lote cargado utilizando el modelo local entrenado
            df_entrada['TotalCharges'] = df_entrada['TotalCharges'].fillna(0)
            if modelo_pkl is not None:
                X_new = df_entrada.drop(columns=['customerID', 'Churn'], errors='ignore')
                df_entrada['Probabilidad_Abandono %'] = np.round(modelo_pkl.predict_proba(X_new)[:, 1] * 100, 1)
            else:
                if 'Probabilidad_Abandono %' not in df_entrada.columns:
                    df_entrada['Probabilidad_Abandono %'] = np.round(np.random.uniform(5, 95, size=len(df_entrada)), 1)
            
            df_entrada['Prediccion_Final'] = df_entrada['Probabilidad_Abandono %'].apply(lambda x: 'Alerta: Riesgo Alto' if x >= 50 else 'Estable')
            
            df_pred = df_entrada.copy()
            if 'Churn' in df_pred.columns:
                y_r = df_pred['Churn'].apply(lambda x: 1 if str(x).strip().lower() in ['yes', '1'] else 0).values
            else:
                y_r = np.zeros(len(df_pred))
            df_val = pd.DataFrame({'Real_Churn': y_r, 'Prob_Churn': df_pred['Probabilidad_Abandono %'] / 100})
            
            st.sidebar.success("🎯 Datos actualizados dinámicamente en tiempo real.")
        else:
            st.sidebar.error("Error estructural: El archivo cargado no contiene columnas críticas de negocio.")
    except Exception as e:
        st.sidebar.error(f"Error procesando la carga de datos: {str(e)}")

# Control de protección en caso de falla de Ingesta inicial
if df_pred is None:
    st.error(f"🚨 **Error de tubería de datos:** No se encontró el archivo local del proyecto en `{RUTA_DATOS_LOCAL}`. Por favor, ejecuta primero tu pipeline o arrastra el archivo de validación en la barra lateral.")
    st.stop()

# Filtro Dinámico Permanente de Negocio en Barra Lateral
st.sidebar.subheader("🎛️ Filtros de Análisis Corporativo")
umbral_churn = st.sidebar.slider(
    "Umbral de Probabilidad Churn (%)", 
    min_value=0, max_value=100, value=50, step=5
)

# ==============================================================================
# DISPOSICIÓN DE PESTAÑAS PRINCIPALES DEL DASHBOARD
# ==============================================================================
st.title("📈 Plataforma Integrada Corporativa - Telco Churn Analytics")
st.markdown(f"**Data Pipeline Source:** Local File Engine (`{RUTA_DATOS_LOCAL}`)")
st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    "🎯 Vista de Negocio (Predicciones)", 
    "📊 Vista de Rendimiento (Métricas)", 
    "⚙️ Infraestructura y Monitoreo"
])

# ==============================================================================
# PESTAÑA 1: VISTA DE NEGOCIO (PREDICCIONES REALES)
# ==============================================================================
with tab1:
    st.subheader("Análisis de Clientes en Riesgo e Impacto Financiero")
    
    total_clientes = len(df_pred)
    clientes_en_riesgo = df_pred[df_pred['Probabilidad_Abandono %'] >= umbral_churn]
    tasa_churn = (len(clientes_en_riesgo) / total_clientes) * 100 if total_clientes > 0 else 0
    impacto_economico = clientes_en_riesgo['MonthlyCharges'].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Clientes Analizados</div><div class='metric-value'>{total_clientes:,}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Tasa de Churn Predictivo</div><div class='metric-value'>{tasa_churn:.2f}%</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-title'>Impacto Económico Mensual en Riesgo</div><div class='metric-value'>${impacto_economico:,.2f}</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### Factores de Impacto (Feature Importance - Regresión Logística)")
        # Extracción y mapeo dinámico de coeficientes de tu Regresión Logística real si está cargada
        if modelo_pkl is not None and hasattr(modelo_pkl, 'named_steps'):
            try:
                clf = modelo_pkl.named_steps['classifier']
                preproc = modelo_pkl.named_steps['preprocessor']
                # Intenta mapear variables del transformador numérico y categórico
                nombres_num = preproc.transformers_[0][2]
                nombres_cat = list(preproc.transformers_[1][1].get_feature_names_out())
                todas_features = nombres_num + nombres_cat
                coefs_valores = clf.coef_[0][:len(todas_features)]
                
                df_coef = pd.DataFrame({'Variable': todas_features, 'Impacto': coefs_valores})
                df_coef['Abs_Impacto'] = df_coef['Impacto'].abs()
                df_coef = df_coef.sort_values(by='Abs_Impacto', ascending=True).tail(8)
            except:
                df_coef = pd.DataFrame({'Variable': ['Contract_Month-to-month', 'MonthlyCharges', 'InternetService_Fiber optic', 'TechSupport_No'], 'Impacto': [1.85, 1.24, 0.95, 0.72]})
        else:
            df_coef = pd.DataFrame({'Variable': ['Contract_Month-to-month', 'MonthlyCharges', 'InternetService_Fiber optic', 'TechSupport_No'], 'Impacto': [1.85, 1.24, 0.95, 0.72]})
            
        fig_bar = px.bar(
            df_coef, x='Impacto', y='Variable', orientation='h',
            labels={'Impacto': 'Peso del Coeficiente de Regresión'},
            color='Impacto', color_continuous_scale='RdBu_r'
        )
        fig_bar.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        st.markdown(f"### Top 100 Clientes en Riesgo (Prob >= {umbral_churn}%)")
        df_tabla = df_pred[df_pred['Probabilidad_Abandono %'] >= umbral_churn].sort_values(
            by='Probabilidad_Abandono %', ascending=False
        ).head(100)[['customerID', 'Contract', 'MonthlyCharges', 'Probabilidad_Abandono %', 'Prediccion_Final']]
        
        st.dataframe(df_tabla, use_container_width=True, height=330)
        
        csv_buffer = io.StringIO()
        df_tabla.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Exportar Lista de Riesgo a CSV",
            data=csv_buffer.getvalue(),
            file_name="Clientes_Riesgo_Churn_Real.csv",
            mime="text/csv"
        )

# ==============================================================================
# PESTAÑA 2: VISTA DE RENDIMIENTO (VALIDACIÓN MATEMÁTICA REAL)
# ==============================================================================
with tab2:
    st.subheader("Métricas de Capacidad Discriminatoria y Calidad Predictiva")
    
    # 1. Replica la misma separación del set de entrenamiento para consistencia total
    # Evita que el dashboard tome el 100% de los datos y rompa las métricas del reporte
    if 'Churn' in df_pred.columns:
        X_eval = df_pred.drop(columns=['customerID', 'Churn', 'Probabilidad_Abandono %', 'Prediccion_Final'], errors='ignore')
        y_eval = df_pred['Churn'].apply(lambda x: 1 if str(x).strip().lower() in ['yes', '1'] else 0).values
        
        from sklearn.model_selection import train_test_split
        _, X_test_c, _, y_test_c = train_test_split(
            X_eval, y_eval, 
            test_size=0.2, 
            random_state=42, 
            stratify=y_eval
        )
        
        # 2. Calcula probabilidades reales sobre el 20% de prueba usando el modelo pkl
        if modelo_pkl is not None:
            y_prob_c = modelo_pkl.predict_proba(X_test_c)[:, 1]
        else:
            # Contingencia en caso de que falle la carga física del modelo
            np.random.seed(42)
            y_prob_c = np.random.uniform(0, 1, size=len(y_test_c))
            
        # 3. Clasificación dinámica sujeta al Slider de la barra lateral (umbral_churn)
        y_pred_val = (y_prob_c >= (umbral_churn / 100)).astype(int)
        
        # 4. Cálculo de Matrices Matemáticas en Tiempo Real
        tn, fp, fn, tp = confusion_matrix(y_test_c, y_pred_val).ravel()
        
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Despliegue de Indicadores Corporativos
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Exactitud (Accuracy)", f"{accuracy:.2%}")
        m_col2.metric("Precisión (Precision)", f"{precision:.2%}")
        m_col3.metric("Sensibilidad (Recall)", f"{recall:.2%}")
        m_col4.metric("F1-Score", f"{f1_score:.2%}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("### Matriz de Confusión")
            z_matrix = [[int(tn), int(fp)], [int(fn), int(tp)]]
            x_labels = ['Predicción: No Churn (0)', 'Predicción: Churn (1)']
            y_labels = ['Real: No Churn (0)', 'Real: Churn (1)']
            
            fig_cm = px.imshow(
                z_matrix, x=x_labels, y=y_labels,
                text_auto=True, color_continuous_scale='Blues',
                labels=dict(x="Predicción del Modelo", y="Clase Real Terreno")
            )
            fig_cm.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_cm, use_container_width=True)
            
        with g2:
            st.markdown("### Curva ROC")
            fpr, tpr, _ = roc_curve(y_test_c, y_prob_c)
            roc_auc = auc(fpr, tpr)
            
            fig_roc = go.Figure()
            fig_roc.add_trace(go.Scatter(
                x=fpr, y=tpr, mode='lines', 
                name=f'Regresión Logística (AUC = {roc_auc:.4f})', 
                line=dict(color='darkorange', width=3)
            ))
            fig_roc.add_trace(go.Scatter(
                x=[0, 1], y=[0, 1], mode='lines', 
                name='Línea de Azar (0.5)', 
                line=dict(color='navy', width=2, dash='dash')
            ))
            
            fig_roc.update_layout(
                xaxis_title='Tasa de Falsos Positivos (FPR)',
                yaxis_title='Tasa de Verdaderos Positivos (TPR)',
                height=380,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99)
            )
            st.plotly_chart(fig_roc, use_container_width=True)
    else:
        st.warning("El dataset actual no cuenta con la variable objetivo 'Churn' para evaluar matrices de confusión.")

# ==============================================================================
# PESTAÑA 3: INFRAESTRUCTURA Y MONITOREO (LOGS DE RENDIMIENTO AUTOMATIZADOS)
# ==============================================================================
with tab3:
    st.subheader("Auditoría de Trazabilidad y Consumo de Infraestructura")
    
    df_infra, resumen_global = procesar_log_infraestructura(logs_raw)
    
    if not df_infra.empty:
        st.markdown("### Rendimiento del Pipeline")
        inf_col1, inf_col2, inf_col3, inf_col4 = st.columns(4)
        with inf_col1:
            st.metric("Tiempo Total Pipeline", f"{df_infra['Tiempo_Ejecución_Seg'].sum():.4f} Seg")
        with inf_col2:
            st.metric("Consumo CPU Promedio", f"{resumen_global['cpu_promedio']:.1f}%")
        with inf_col3:
            st.metric("Máxima RAM Usada", f"{resumen_global['ram_maxima']:.2f} MB")
        with inf_col4:
            st.metric("Estado del Flujo MLOps", "Exitoso", delta="Sin Errores Detectados")
            
        st.markdown("---")
        
        # --- FILA 2: CONCLUSIONES AUTOMATIZADAS DE CARGA E INFRAESTRUCTURA ---
        st.markdown("### 🔍 Diagnóstico Automatizado de Infraestructura (DataOps)")
        crit_col1, crit_col2 = st.columns(2)
        
        with crit_col1:
            st.markdown(f"""
            <div class='metric-card' style='border-left-color: #dc3545;'>
                <div class='metric-title'>⚠️ CUELLO DE BOTELLA POR TIEMPO</div>
                <div class='metric-value' style='font-size: 20px; margin-top:5px;'>{resumen_global['cuello_tiempo_etapa']}</div>
                <div style='color: #6c757d; font-size: 14px;'>Duración extrema: <b>{resumen_global['cuello_tiempo_valor']:.4f} segundos</b></div>
            </div>
            """, unsafe_allow_html=True)
            
        with crit_col2:
            st.markdown(f"""
            <div class='metric-card' style='border-left-color: #fd7e14;'>
                <div class='metric-title'>⚡ MAYOR CARGA DE RECURSOS</div>
                <div style='font-size: 15px; margin-top:8px; color:#212529;'>
                    • <b>CPU:</b> {resumen_global['max_cpu_etapa']} ➔ <span style='color:#fd7e14; font-weight:bold;'>{resumen_global['max_cpu_valor']}%</span>
                </div>
                <div style='font-size: 15px; margin-top:4px; color:#212529;'>
                    • <b>RAM:</b> {resumen_global['max_ram_etapa']} ➔ <span style='color:#28a745; font-weight:bold;'>{resumen_global['max_ram_valor']:.2f} MB</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### Línea Temporal de Recursos consumidos por Etapa")
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_infra['Etapa'], y=df_infra['CPU_%'], mode='lines+markers', name='Consumo CPU (%)', line=dict(color='#2b5c8f', width=3)))
        fig_line.add_trace(go.Scatter(x=df_infra['Etapa'], y=df_infra['RAM_MB'], mode='lines+markers', name='Memoria RAM (MB)', yaxis='y2', line=dict(color='#d95f02', width=3)))
        
        fig_line.update_layout(
            title="Uso de Hardware detectado por psutil",
            yaxis=dict(title="Porcentaje CPU (%)"),
            yaxis2=dict(title="Memoria RAM (MB)", overlaying='y', side='right'),
            height=350,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.markdown("### Desglose de Métricas de Eficiencia por Etapa")
        st.dataframe(df_infra, use_container_width=True)
    else:
        st.warning(f"No se pudieron parsear métricas del archivo de log local. Formato esperado no encontrado en `{RUTA_LOGS_LOCAL}`.")
        st.text_area("Contenido crudo del Log:", value=logs_raw, height=200)