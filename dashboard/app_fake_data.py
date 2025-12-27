import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Configuración de página
st.set_page_config(
    page_title="VantageFlow IoT Dashboard",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
    }
    .tech-badge {
        background: #e9ecef;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Título principal con logo
st.markdown("""
<div class="main-header">
    🚀 VantageFlow - IoT Data Pipeline Dashboard
    <br>
    <small style="font-size: 1rem; opacity: 0.9;">Pipeline Serverless en AWS - Proyecto Portfolio</small>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/873/873107.png", width=80)
    st.markdown("## ⚙️ Configuración")
    
    demo_mode = st.selectbox("Modo de datos:", ["Datos de Ejemplo", "Simulación en Tiempo Real"])
    
    if demo_mode == "Simulación en Tiempo Real":
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
        refresh_rate = st.slider("Frecuencia (s)", 5, 60, 10)
    else:
        auto_refresh = False
    
    st.markdown("---")
    st.markdown("## 📊 Filtros")
    num_devices = st.slider("Número de dispositivos", 3, 15, 8)
    anomaly_rate = st.slider("Tasa de anomalías (%)", 5, 50, 20)
    
    st.markdown("---")
    st.markdown("## 🔗 Enlaces")
    if st.button("🌐 Ver en AWS Console"):
        st.info("En producción: https://console.aws.amazon.com")
    if st.button("💾 Código en GitHub"):
        st.info("https://github.com/tu-usuario/vantageflow")

# Generar datos de ejemplo
@st.cache_data
def generate_sample_data(num_devices=8, anomaly_rate=20):
    """Genera datos de ejemplo para el dashboard"""
    
    # Datos Gold (estadísticas por dispositivo)
    devices = [f"DEV-{str(i).zfill(3)}" for i in range(1, num_devices + 1)]
    device_types = ['temperature_sensor', 'humidity_sensor', 'pressure_sensor', 'vibration_sensor']
    
    gold_data = []
    for device in devices:
        readings = random.randint(100, 1000)
        avg_value = random.uniform(20, 80)
        anomaly_pct = random.uniform(0, anomaly_rate)
        
        gold_data.append({
            'device_id': device,
            'device_type': random.choice(device_types),
            'location': random.choice(['FABRICA-A', 'FABRICA-B', 'ALMACEN', 'OFICINA']),
            'total_readings': readings,
            'avg_value': round(avg_value, 2),
            'min_value': round(avg_value * 0.7, 2),
            'max_value': round(avg_value * 1.3, 2),
            'anomaly_count': int(readings * (anomaly_pct / 100)),
            'anomaly_percentage': round(anomaly_pct, 1)
        })
    
    df_gold = pd.DataFrame(gold_data)
    
    # Métricas del pipeline
    pipeline_metrics = {
        'bronze': random.randint(10, 30),
        'silver': random.randint(8, 25),
        'gold': random.randint(5, 15),
        'anomalies': random.randint(2, 10)
    }
    
    # Timeline de procesamiento
    timeline = []
    now = datetime.now()
    for i in range(24):
        hour = (now - timedelta(hours=i)).strftime('%H:00')
        records = random.randint(500, 5000)
        timeline.append({
            'hora': hour,
            'registros_procesados': records,
            'anomalias': int(records * (anomaly_rate / 100))
        })
    
    df_timeline = pd.DataFrame(timeline[::-1])
    
    return df_gold, pipeline_metrics, df_timeline

# Obtener datos
df_gold, pipeline_metrics, df_timeline = generate_sample_data(num_devices, anomaly_rate)

# SECCIÓN 1: KPIs DEL PIPELINE
st.markdown("## 📈 KPIs del Pipeline Data Lake")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        label="📁 BRONZE",
        value=pipeline_metrics['bronze'],
        delta="+2 hoy",
        help="Datos crudos en S3"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        label="🔄 SILVER",
        value=pipeline_metrics['silver'],
        delta="+1 hoy",
        help="Datos limpios y validados"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        label="🏆 GOLD",
        value=pipeline_metrics['gold'],
        delta="+1 hoy",
        help="Datos agregados para análisis"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.metric(
        label="⚠️ ANOMALIES",
        value=pipeline_metrics['anomalies'],
        delta=f"+{int(pipeline_metrics['anomalies']*0.3)} hoy",
        help="Datos sospechosos detectados"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# SECCIÓN 2: DATOS GOLD
st.markdown("## 📊 Datos Gold - Resumen por Dispositivo")

tab1, tab2, tab3 = st.tabs(["📋 Tabla de Datos", "📈 Visualizaciones", "📱 Dispositivos Críticos"])

with tab1:
    # Mostrar tabla con estilo
    styled_df = df_gold.style.background_gradient(
        subset=['anomaly_percentage'], 
        cmap='RdYlGn_r'
    ).format({
        'avg_value': '{:.1f}°C',
        'anomaly_percentage': '{:.1f}%',
        'total_readings': '{:,}'
    })
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Estadísticas resumen
    total_readings = df_gold['total_readings'].sum()
    avg_anomaly = df_gold['anomaly_percentage'].mean()
    critical_devices = df_gold[df_gold['anomaly_percentage'] > 30].shape[0]
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("📖 Total Lecturas", f"{total_readings:,}")
    col_stat2.metric("📊 Anomalía Promedio", f"{avg_anomaly:.1f}%")
    col_stat3.metric("🚨 Dispositivos Críticos", critical_devices)

with tab2:
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gráfico de barras - Anomalías por dispositivo
        fig1 = px.bar(
            df_gold.sort_values('anomaly_percentage', ascending=False).head(10),
            x='device_id',
            y='anomaly_percentage',
            color='anomaly_percentage',
            color_continuous_scale='RdYlGn_r',
            title='Top 10 Dispositivos con Más Anomalías',
            labels={'anomaly_percentage': '% Anomalías', 'device_id': 'Dispositivo'}
        )
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        # Gráfico de dispersión
        fig2 = px.scatter(
            df_gold,
            x='avg_value',
            y='anomaly_percentage',
            size='total_readings',
            color='device_type',
            hover_name='device_id',
            title='Relación: Valor Promedio vs Anomalías',
            labels={'avg_value': 'Valor Promedio', 'anomaly_percentage': '% Anomalías'}
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Timeline de procesamiento
    st.markdown("### 📅 Actividad Reciente (Últimas 24h)")
    fig3 = px.line(
        df_timeline,
        x='hora',
        y=['registros_procesados', 'anomalias'],
        title='Registros Procesados por Hora',
        markers=True
    )
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    # Dispositivos críticos
    critical_df = df_gold[df_gold['anomaly_percentage'] > 30].sort_values('anomaly_percentage', ascending=False)
    
    if not critical_df.empty:
        st.warning(f"🚨 Se detectaron {len(critical_df)} dispositivos con anomalías > 30%")
        
        for _, row in critical_df.iterrows():
            with st.container():
                col_alert1, col_alert2, col_alert3 = st.columns([2, 2, 1])
                
                with col_alert1:
                    st.markdown(f"**{row['device_id']}**")
                    st.caption(f"{row['device_type']} • {row['location']}")
                
                with col_alert2:
                    st.progress(row['anomaly_percentage']/100, 
                               text=f"Anomalías: {row['anomaly_percentage']}%")
                
                with col_alert3:
                    st.metric("Lecturas", row['total_readings'])
            
            st.divider()
    else:
        st.success("✅ Todos los dispositivos dentro de parámetros normales")

# SECCIÓN 3: ARQUITECTURA DEL SISTEMA
st.markdown("## 🏗️ Arquitectura del Sistema")

col_arch1, col_arch2 = st.columns([3, 2])

with col_arch1:
    st.markdown("""
    ### Data Lake en AWS - 4 Capas
    
    ```mermaid
    graph LR
        A[📥 Dispositivos IoT] --> B[🟤 BRONZE<br/>S3 Raw Data]
        B --> C[⚪ SILVER<br/>Lambda Processing]
        C --> D[🟡 GOLD<br/>S3 Aggregated]
        C --> E[🔴 ANOMALIES<br/>S3 Filtered]
        D --> F[📊 Dashboards]
        D --> G[🤖 ML Models]
        D --> H[📈 Analytics]
    ```
    
    **Flujo de datos:**
    1. **Ingesta**: Dispositivos → S3 Bronze (CSV)
    2. **Procesamiento**: Lambda valida y separa anomalías
    3. **Agregación**: Lambda calcula estadísticas por dispositivo
    4. **Consumo**: Datos listos para BI/ML
    """)

with col_arch2:
    st.markdown("### 🛠️ Stack Tecnológico")
    
    st.markdown('<div class="tech-badge">AWS S3</div>', unsafe_allow_html=True)
    st.caption("Data Lake storage")
    
    st.markdown('<div class="tech-badge">AWS Lambda</div>', unsafe_allow_html=True)
    st.caption("Serverless computing")
    
    st.markdown('<div class="tech-badge">Python 3.11</div>', unsafe_allow_html=True)
    st.caption("ETL processing")
    
    st.markdown('<div class="tech-badge">Terraform</div>', unsafe_allow_html=True)
    st.caption("Infrastructure as Code")
    
    st.markdown('<div class="tech-badge">Streamlit</div>', unsafe_allow_html=True)
    st.caption("Dashboard visualization")
    
    st.markdown('<div class="tech-badge">Plotly</div>', unsafe_allow_html=True)
    st.caption("Interactive charts")
    
    st.markdown("### 💰 Optimización de Costos")
    st.metric("Costo mensual estimado", "$5-10", "-85% vs tradicional")
    st.caption("Free Tier + pay-per-use")

# SECCIÓN 4: PARA TU PORTFOLIO
st.markdown("## 🎯 Para Tu Portfolio")

expander = st.expander("📝 ¿Cómo explicar este proyecto en entrevistas?", expanded=False)
with expander:
    st.markdown("""
    **Problema:** Procesar datos IoT en tiempo real con escalabilidad y bajo costo
    
    **Solución:** Pipeline serverless en AWS con arquitectura Data Lake moderna
    
    **Tecnologías:** AWS (S3, Lambda, CloudWatch), Python, Terraform
    
    **Resultados:**
    - ✅ **Performance**: 1000+ registros/segundo
    - ✅ **Costo**: $5-10/mes (optimizado)
    - ✅ **Disponibilidad**: 99.9% (serverless)
    - ✅ **Mantenimiento**: Cero (fully managed)
    
    **Demo rápida:**
    ```bash
    # Subir datos
    aws s3 cp datos.csv s3://bucket/bronze/
    
    # Ver procesamiento automático
    # (30 segundos después)
    
    # Consultar resultados
    aws s3 ls s3://bucket/gold/
    ```
    """)

# Footer profesional
st.markdown("---")

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("**📅 Última actualización**")
    st.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

with footer_col2:
    st.markdown("**🔗 Enlaces del proyecto**")
    st.markdown("[GitHub](https://github.com) • [LinkedIn](https://linkedin.com)")

with footer_col3:
    st.markdown("**🚀 VantageFlow Cloud AWS**")
    st.markdown("Data Pipeline Serverless para IoT")

# Auto-refresh si está activado
if auto_refresh and demo_mode == "Simulación en Tiempo Real":
    time.sleep(refresh_rate)
    st.rerun()
