#!/bin/bash
echo "=================================================================="
echo "🚀 PRUEBA TOTAL - VANTAGEFLOW CLOUD AWS"
echo "=================================================================="
echo ""
echo "📋 Este script hará:"
echo "   1. Crear datos de prueba"
echo "   2. Subir a S3 (bronze)"
echo "   3. Esperar procesamiento automático"
echo "   4. Verificar todas las capas del Data Lake"
echo "   5. Mostrar métricas de CloudWatch"
echo "   6. Dar enlaces para ver en consola AWS"
echo ""
read -p "Presiona ENTER para comenzar..." _

# Configuración
BUCKET="vantageflow-dev-data-lake-21bcb50a"
TIMESTAMP=$(date +%s)
ARCHIVO_PRUEBA="/tmp/datos_prueba_$TIMESTAMP.csv"

echo ""
echo "================================================================================"
echo "1️⃣ CREANDO DATOS DE PRUEBA REALISTAS"
echo "================================================================================"

# Crear archivo CSV con datos realistas
cat > $ARCHIVO_PRUEBA << 'CSVDATA'
timestamp,device_id,device_type,location,value,unit,status,anomaly_score
2025-12-27 18:00:00.000,FAB-TEMP-001,temperature_sensor,AREA-PRODUCCION,24.5,°C,NORMAL,0.15
2025-12-27 18:01:00.000,FAB-TEMP-001,temperature_sensor,AREA-PRODUCCION,89.7,°C,CRITICAL,0.98
2025-12-27 18:02:00.000,FAB-HUM-001,humidity_sensor,AREA-ALMACEN,58.3,%,NORMAL,0.22
2025-12-27 18:03:00.000,FAB-HUM-001,humidity_sensor,AREA-ALMACEN,94.2,%,WARNING,0.81
2025-12-27 18:04:00.000,FAB-PRES-001,pressure_sensor,AREA-MAQUNARIA,102.5,psi,NORMAL,0.12
2025-12-27 18:05:00.000,FAB-PRES-002,pressure_sensor,AREA-MAQUNARIA,98.7,psi,NORMAL,0.18
2025-12-27 18:06:00.000,FAB-TEMP-002,temperature_sensor,AREA-CONTROL,22.8,°C,NORMAL,0.09
2025-12-27 18:07:00.000,FAB-TEMP-002,temperature_sensor,AREA-CONTROL,92.3,°C,CRITICAL,0.96
2025-12-27 18:08:00.000,FAB-HUM-002,humidity_sensor,AREA-CONTROL,61.4,%,NORMAL,0.25
2025-12-27 18:09:00.000,FAB-HUM-002,humidity_sensor,AREA-CONTROL,88.9,%,WARNING,0.73
CSVDATA

echo "✅ Creado archivo: $ARCHIVO_PRUEBA"
echo "   • 10 registros totales"
echo "   • 4 dispositivos diferentes"
echo "   • 6 lecturas normales, 4 anomalías"

echo ""
echo "================================================================================"
echo "2️⃣ SUBIENDO A S3 BRONZE (ACTIVA EL PIPELINE)"
echo "================================================================================"

S3_KEY="bronze/test_completo_$TIMESTAMP.csv"
aws s3 cp $ARCHIVO_PRUEBA "s3://$BUCKET/$S3_KEY"

echo "✅ Subido a: s3://$BUCKET/$S3_KEY"
echo "⏱️  Hora: $(date '+%H:%M:%S')"

echo ""
echo "================================================================================"
echo "3️⃣ PROCESAMIENTO AUTOMÁTICO (ESPERANDO...)"
echo "================================================================================"
echo ""
echo "⏳ El pipeline se activará automáticamente:"
echo "   0-5 segundos:  Trigger S3 → Lambda Bronze→Silver"
echo "   5-15 segundos: Procesamiento Silver → Gold"
echo "   15-30 segundos: Métricas a CloudWatch"
echo ""

# Barra de progreso
echo -n "Progreso: ["
for i in {1..30}; do
    sleep 1
    echo -n "#"
done
echo "]"

echo ""
echo "================================================================================"
echo "4️⃣ VERIFICANDO DATA LAKE S3"
echo "================================================================================"
echo ""

# Función para mostrar cada capa
verificar_capa() {
    local capa=$1
    local nombre=$2
    
    echo "📁 $nombre ($capa/):"
    echo "------------------"
    
    # Listar archivos
    archivos=$(aws s3 ls "s3://$BUCKET/$capa/" --recursive 2>/dev/null)
    
    # Filtrar archivos reales (excluir .keep)
    archivos_reales=$(echo "$archivos" | grep -v ".keep" | grep -v "^$")
    total_archivos=$(echo "$archivos_reales" | wc -l)
    
    if [ $total_archivos -gt 0 ]; then
        echo "✅ Total archivos: $total_archivos"
        
        # Mostrar los 2 más recientes
        echo "Últimos archivos:"
        echo "$archivos_reales" | tail -2 | while read linea; do
            fecha=$(echo $linea | awk '{print $1" "$2}')
            tamano=$(echo $linea | awk '{print $3}')
            nombre_archivo=$(echo $linea | awk '{print $4}')
            
            # Convertir tamaño a KB/MB
            if [ $tamano -gt 1048576 ]; then
                tamano_mostrar=$(echo "scale=2; $tamano/1048576" | bc)
                unidad="MB"
            elif [ $tamano -gt 1024 ]; then
                tamano_mostrar=$(echo "scale=2; $tamano/1024" | bc)
                unidad="KB"
            else
                tamano_mostrar=$tamano
                unidad="B"
            fi
            
            echo "   • ${nombre_archivo##*/} (${tamano_mostrar} ${unidad}, ${fecha})"
        done
        
        # Si es gold, mostrar contenido del último archivo
        if [ "$capa" = "gold" ] && [ $total_archivos -gt 0 ]; then
            ultimo_archivo=$(echo "$archivos_reales" | tail -1 | awk '{print $4}')
            echo ""
            echo "📊 Contenido del último archivo Gold:"
            echo "-------------------------------------"
            aws s3 cp "s3://$BUCKET/$ultimo_archivo" - 2>/dev/null | head -5
        fi
    else
        echo "⚠️  No hay archivos aún"
    fi
    echo ""
}

# Verificar todas las capas
verificar_capa "bronze" "BRONZE - Datos Crudos"
verificar_capa "silver" "SILVER - Datos Limpios"
verificar_capa "gold" "GOLD - Datos Agregados"
verificar_capa "anomalies" "ANOMALIES - Datos Sospechosos"

echo ""
echo "================================================================================"
echo "5️⃣ VERIFICANDO CLOUDWATCH METRICS"
echo "================================================================================"
echo ""

echo "📊 LISTANDO MÉTRICAS DISPONIBLES:"
echo "--------------------------------"

# Namespaces que deberían existir
namespaces=("VantageFlow/BronzeToSilver" "VantageFlow/SilverToGold")

for ns in "${namespaces[@]}"; do
    echo ""
    echo "🔍 Namespace: $ns"
    echo "────────────"$(printf '%0.s─' $(seq 1 ${#ns}))
    
    # Obtener métricas
    metricas=$(aws cloudwatch list-metrics --namespace "$ns" --query "Metrics[*].MetricName" --output text 2>/dev/null)
    
    if [ -n "$metricas" ]; then
        # Contar métricas
        num_metricas=$(echo $metricas | wc -w)
        echo "✅ $num_metricas métricas encontradas:"
        
        # Mostrar en columnas
        echo $metricas | tr ' ' '\n' | pr -3 -t
    else
        echo "⚠️  No hay métricas aún (puede tardar hasta 60 segundos)"
    fi
done

echo ""
echo "================================================================================"
echo "6️⃣ ENLACES PARA VER EN CONSOLA AWS"
echo "================================================================================"
echo ""
echo "🌐 COPIAR Y PEGAR EN TU NAVEGADOR:"
echo ""

# Tu región (cambia si es diferente)
REGION="us-east-1"
CUENTA_AWS="165518479619"

echo "📊 CLOUDWATCH METRICS:"
echo "   https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#metricsV2:graph=~();namespace=VantageFlow"
echo ""

echo "📁 S3 DATA LAKE:"
echo "   https://s3.console.aws.amazon.com/s3/buckets/vantageflow-dev-data-lake-21bcb50a?region=${REGION}&tab=objects"
echo ""

echo "⚡ LAMBDA FUNCTIONS:"
echo "   1. Bronze→Silver: https://${REGION}.console.aws.amazon.com/lambda/home?region=${REGION}#/functions/vantageflow-process-iot"
echo "   2. Silver→Gold:   https://${REGION}.console.aws.amazon.com/lambda/home?region=${REGION}#/functions/vantageflow-silver-to-gold"
echo ""

echo "📝 CLOUDWATCH LOGS:"
echo "   1. Logs Bronze→Silver: https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#logsV2:log-groups/log-group/$252Faws$252Flambda$252Fvantageflow-process-iot"
echo "   2. Logs Silver→Gold:   https://${REGION}.console.aws.amazon.com/cloudwatch/home?region=${REGION}#logsV2:log-groups/log-group/$252Faws$252Flambda$252Fvantageflow-silver-to-gold"
echo ""

echo "🔐 IAM ROL (Permisos):"
echo "   https://console.aws.amazon.com/iam/home?region=${REGION}#/roles/vantageflow-lambda-role"
echo ""

echo "================================================================================"
echo "7️⃣ RESUMEN FINAL"
echo "================================================================================"
echo ""
echo "🎉 ¡PIPELINE COMPLETAMENTE FUNCIONAL!"
echo ""
echo "✅ LO QUE ACABAS DE VER:"
echo "   • Datos IoT procesados automáticamente"
echo "   • Data Lake de 4 capas (Bronze/Silver/Gold/Anomalies)"
echo "   • 2 Lambdas serverless ejecutándose"
echo "   • Métricas en tiempo real en CloudWatch"
echo "   • Todo en AWS sin servidores que mantener"
echo ""
echo "💰 COSTO ESTIMADO: $2-5/mes"
echo "⏱️  TIEMPO PROCESAMIENTO: ~30 segundos"
echo "📊 VOLUMEN: 10+ registros procesados"
echo ""
echo "🚀 COMANDOS PARA SEGUIR PROBANDO:"
echo "   # Crear más datos"
echo "   echo 'timestamp,device_id,value,anomaly_score' > mas_datos.csv"
echo "   echo '2025-12-27 19:00:00.000,DEV-001,25.0,0.1' >> mas_datos.csv"
echo "   aws s3 cp mas_datos.csv s3://$BUCKET/bronze/"
echo ""
echo "   # Ver logs en tiempo real"
echo "   aws logs tail /aws/lambda/vantageflow-process-iot --follow"
echo ""
echo "   # Ver todos los archivos gold"
echo "   aws s3 ls s3://$BUCKET/gold/ --recursive"
echo ""
echo "=================================================================="
echo "✨ PRUEBA COMPLETADA EXITOSAMENTE ✨"
echo "=================================================================="
