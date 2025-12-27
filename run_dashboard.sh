#!/bin/bash
echo "🚀 INICIANDO DASHBOARD VANTAGEFLOW"
echo "=================================="

# Navegar al directorio del dashboard
cd /home/pashitox/Documentos/VantageFlow-Cloud-AWS/dashboard

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "✅ Dependencias instaladas"
echo ""
echo "🌐 Abriendo dashboard en:"
echo "   http://localhost:8501"
echo ""
echo "📋 Credenciales AWS necesarias:"
echo "   • AWS_ACCESS_KEY_ID"
echo "   • AWS_SECRET_ACCESS_KEY"
echo "   • AWS_DEFAULT_REGION=us-east-1"
echo ""
echo "🔄 Iniciando Streamlit..."
echo ""
echo "💡 Presiona Ctrl+C para detener"

# Ejecutar Streamlit
streamlit run app.py
