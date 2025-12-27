import streamlit as st
import pandas as pd
import boto3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io
import time

# Configuración de página
st.set_page_config(
    page_title="VantageFlow IoT Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .section-header {
        color: #1E3A8A;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">🚀 VantageFlow - IoT Data Pipeline Dashboard</h1>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <p style='color: #666; font-size: 1.1rem;'>
    Dashboard en tiempo real para monitorear el pipeline de datos IoT en AWS
    </p>
</div>
""", unsafe_allow_html=True)

# Inicializar cliente S3
@st.cache_resource
def get_s3_client():
    return boto3.client('s3')

# Función para obtener datos
@st.cache_data(ttl=60)
def get_pipeline_data():
    """Obtiene datos del pipeline desde S3"""
    s3 = get_s3_client()
    bucket = "vantageflow-dev-data-lake-21bcb50a"
    
    data = {
        'layers': {},
        'latest_gold': None,
        'latest_gold_df': pd.DataFrame(),
        'file_info': {},
        'timestamps': {}
    }
    
    try:
        # 1. Contar archivos por capa
        for layer in ['bronze', 'silver', 'gold', 'anomalies']:
            try:
                response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{layer}/")
                files = [obj for obj in response.get('Contents', []) 
                        if not obj['Key'].endswith('.keep')]
                data['layers'][layer] = len(files)
                
                # Obtener último archivo de cada capa
                if files:
                    latest_file = max(files, key=lambda x: x['LastModified'])
                    data['file_info'][layer] = {
                        'name': latest_file['Key'].split('/')[-1],
                        'size_mb': latest_file['Size'] / (1024 * 1024),
                        'last_modified': latest_file['LastModified']
                    }
            except Exception as e:
                data['layers'][layer] = 0
        
        # 2. Obtener datos Gold más recientes
        if data['layers'].get('gold', 0) > 0:
            try:
                response = s3.list_objects_v2(Bucket=bucket, Prefix="gold/")
                files = [obj for obj in response.get('Contents', []) 
                        if not obj['Key'].endswith('.keep')]
                
                if files:
                    latest_gold = max(files, key=lambda x: x['LastModified'])
                    data['latest_gold'] = latest_gold['Key']
                    
                    # Descargar y leer datos
                    obj = s3.get_object(Bucket=bucket, Key=latest_gold['Key'])
                    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
                    data['latest_gold_df'] = df
                    
                    # Estadísticas
                    if not df.empty:
                        data['stats'] = {
                            'total_devices': df['device_id'].nunique(),
                            'avg_anomaly': df['anomaly_percentage'].mean(),
                            'max_anomaly': df['anomaly_percentage'].max(),
                            'total_readings': df['total_readings'].sum() if 'total_readings' in df.columns else 0
                        }
            except Exception as e:
                st.sidebar.warning(f"Error cargando datos Gold: {e}")
        
        # 3. Obtener datos de anomalías
        if data['layers'].get('anomalies', 0) > 0:
            try:
                response = s3.list_objects_v2(Bucket=bucket, Prefix="anomalies/")
                files = [obj for obj in response.get('Contents', []) 
                        if not obj['Key'].endswith('.keep')]
                
                if files:
                    latest_anomaly = max(files, key=lambda x: x['LastModified'])
                    obj = s3.get_object(Bucket=bucket, Key=latest_anomaly['Key'])
                    anomaly_df = pd.read_csv(io.BytesIO(obj['Body'].read()))
                    
                    if not anomaly_df.empty:
                        data['anomaly_stats'] = {
                            'total_anomalies': len(anomaly_df),
                            'top_device': anomaly_df['device_id'].mode()[0] if not anomaly_df['device_id'].mode().empty else 'N/A',
                            'avg_anomaly_score': anomaly_df['anomaly_score'].astype(float).mean() if 'anomaly_score' in anomaly_df.columns else 0
                        }
            except:
                pass
                
    except Exception as e:
        st.error(f"Error conectando a AWS: {e}")
    
    data['timestamp'] = datetime.now()
    return data

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    
    auto_refresh = st.checkbox("�� Auto-refresh", value=True, help="Actualizar automáticamente cada 30 segundos")
    refresh_rate = st.slider("Frecuencia (segundos)", 10, 120, 30)
    
    st.markdown("---")
    st.markdown("## 📊 Filtros")
    
    show_details = st.checkbox("Mostrar detalles técnicos", value=False)
    
    st.markdown("---")
    st.markdown("## 🔗 Enlaces AWS")
    
    if st.button("🌐 CloudWatch Metrics"):
        st.write("https://us-east-1.console.aws.amazon.com/cloudwatch")
    
    if st.button("📁 S3 Data Lake"):
        st.write("https://s3.console.aws.amazon.com/s3/buckets/vantageflow-dev-data-lake-21bcb50a")
    
    st.markdown("---")
    st.markdown("### 📈 Estado del Sistema")
    
    # Indicador de conexión
    try:
        s3 = get_s3_client()
        s3.list_buckets()
        st.success("✅ Conectado a AWS")
    except:
        st.error("❌ Error de conexión AWS")

# Obtener datos
data = get_pipeline_data()

# Sección 1: KPIs principales
st.markdown('<h2 class="section-header">📈 KPIs del Pipeline</h2>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📁 Datos Crudos",
        value=data['layers'].get('bronze', 0),
        help="Archivos en capa Bronze"
    )

with col2:
    st.metric(
        label="🔄 Datos Procesados", 
        value=data['layers'].get('silver', 0),
        help="Archivos en capa Silver"
    )

with col3:
    st.metric(
        label="🏆 Datos Analíticos",
        value=data['layers'].get('gold', 0),
        help="Archivos en capa Gold"
    )

with col4:
    st.metric(
        label="⚠️ Anomalías Detectadas",
        value=data['layers'].get('anomalies', 0),
        help="Archivos en capa Anomalies"
    )

# Sección 2: Datos Gold
st.markdown('<h2 class="section-header">📊 Datos Gold - Resumen por Dispositivo</h2>', unsafe_allow_html=True)

if not data['latest_gold_df'].empty:
    df = data['latest_gold_df']
    
    # Mostrar tabla
    st.dataframe(df, use_container_width=True, height=300)
    
    # Gráficos
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Gráfico de barras
        if 'device_id' in df.columns and 'anomaly_percentage' in df.columns:
            fig1 = px.bar(
                df,
                x='device_id',
                y='anomaly_percentage',
                title='📈 Porcentaje de Anomalías por Dispositivo'
            )
            st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        # Gráfico de dispersión
        if 'avg_value' in df.columns and 'anomaly_percentage' in df.columns:
            fig2 = px.scatter(
                df,
                x='avg_value',
                y='anomaly_percentage',
                title='🔍 Valor Promedio vs Anomalías'
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    # Estadísticas
    if 'stats' in data:
        st.markdown("### 📋 Estadísticas Resumen")
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.metric("Dispositivos Únicos", data['stats']['total_devices'])
        
        with col_stats2:
            st.metric("Anomalía Promedio", f"{data['stats']['avg_anomaly']:.1f}%")
        
        with col_stats3:
            st.metric("Anomalía Máxima", f"{data['stats']['max_anomaly']:.1f}%")
    
else:
    st.info("📭 No hay datos Gold disponibles. Sube datos a la capa Bronze para comenzar.")
    
    with st.expander("🔼 ¿Cómo subir datos de prueba?"):
        st.code("""
# Crear archivo de prueba
cat > prueba.csv << 'CSV'
timestamp,device_id,device_type,value,anomaly_score
2024-01-01 10:00:00.000,DEV-001,temperature_sensor,25.0,0.1
2024-01-01 10:01:00.000,DEV-001,temperature_sensor,85.0,0.9
CSV

# Subir a S3
aws s3 cp prueba.csv s3://vantageflow-dev-data-lake-21bcb50a/bronze/
""", language="bash")

# Sección 3: Información del Sistema
st.markdown('<h2 class="section-header">⚙️ Información del Sistema</h2>', unsafe_allow_html=True)

col_info1, col_info2 = st.columns(2)

with col_info1:
    st.markdown("### 📁 Últimos Archivos")
    for layer, info in data.get('file_info', {}).items():
        if info:
            st.write(f"**{layer.title()}**:")
            st.write(f"• Archivo: `{info['name'][:20]}...`")
            st.write(f"• Tamaño: {info['size_mb']:.2f} MB")
            st.write(f"• Actualizado: {info['last_modified'].strftime('%H:%M:%S')}")

with col_info2:
    st.markdown("### 🔧 Arquitectura")
    st.markdown("""
    **Data Lake en AWS:**
    - 🟤 **Bronze**: Datos crudos (S3)
    - ⚪ **Silver**: Datos limpios (Lambda)
    - 🟡 **Gold**: Datos agregados
    - 🔴 **Anomalies**: Datos sospechosos
    
    **Tecnologías:**
    - Python 3.11
    - AWS Lambda + S3
    - Terraform (IaC)
    - Streamlit (Dashboard)
    """)

# Footer
st.markdown("---")
st.markdown(f"**🔄 Última actualización:** {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("**🚀 VantageFlow Cloud AWS** - Pipeline de datos IoT Serverless")

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
