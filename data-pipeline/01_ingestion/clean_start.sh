# /home/pashitox/Documentos/VantageFlow-Cloud-AWS/data-pipeline/01_ingestion/clean_start.sh
#!/bin/bash

echo "🧹 INICIANDO LIMPIEZA PROFESIONAL"
echo "================================="

# Configuración
BUCKET="vantageflow-dev-data-lake-21bcb50a"
LOCAL_DIRS=(
    "/home/pashitox/Documentos/VantageFlow-Cloud-AWS/data/raw"
    "/home/pashitox/Documentos/VantageFlow-Cloud-AWS/data/processed"
)

# 1. Limpiar S3 (manteniendo estructura)
echo ""
echo "1. Limpiando capas S3..."
for layer in bronze silver gold anomalies; do
    echo "   Limpiando $layer..."
    # Listar y eliminar archivos (no carpetas)
    aws s3 rm "s3://$BUCKET/$layer/" --recursive --exclude "*" --include "*.csv" --include "*.parquet" 2>/dev/null || true
    echo "   ✅ $layer limpiado"
done

# Crear archivos vacíos para mantener estructura
echo "   Creando estructura base..."
touch /tmp/empty.csv
aws s3 cp /tmp/empty.csv "s3://$BUCKET/bronze/.keep" 2>/dev/null || true
aws s3 cp /tmp/empty.csv "s3://$BUCKET/silver/.keep" 2>/dev/null || true
aws s3 cp /tmp/empty.csv "s3://$BUCKET/gold/.keep" 2>/dev/null || true
aws s3 cp /tmp/empty.csv "s3://$BUCKET/anomalies/.keep" 2>/dev/null || true
rm /tmp/empty.csv

# 2. Limpiar directorios locales
echo ""
echo "2. Limpiando directorios locales..."
for dir in "${LOCAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "   Limpiando $dir..."
        # Mantener solo los últimos 5 archivos por seguridad
        find "$dir" -name "*.csv" -type f | sort -r | tail -n +6 | xargs rm -f 2>/dev/null || true
        echo "   ✅ $dir limpiado"
    else
        echo "   Creando $dir..."
        mkdir -p "$dir"
    fi
done

# 3. Verificar CloudWatch Logs
echo ""
echo "3. Verificando estado del pipeline..."
echo "   Lambdas:"
aws lambda list-functions --query "Functions[?contains(FunctionName, 'vantageflow')].FunctionName" --output text | tr '\t' '\n' | while read lambda; do
    echo "   • $lambda"
done

echo ""
echo "4. Configuración actual:"
echo "   Bucket S3: $BUCKET"
echo "   Triggers activos:"
aws s3api get-bucket-notification-configuration --bucket "$BUCKET" --query "LambdaFunctionConfigurations[*].Filter.Key.FilterRules[0].Value" --output text | tr '\t' '\n' | while read prefix; do
    echo "   • $prefix"
done

echo ""
echo "🎯 LISTO PARA INGESTA NUEVA"
echo "   Ejecuta: python3 s3_data_ingestor.py --batches 3 --records 200"
echo ""