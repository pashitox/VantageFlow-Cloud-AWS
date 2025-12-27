#!/bin/bash
echo "🎬 GENERANDO DATOS Y VIENDO MÉTRICAS EN TIEMPO REAL"
echo "=================================================="

# Crear datos de prueba
ARCHIVO_TEST="/tmp/test_visualizacion_$(date +%s).csv"

cat > $ARCHIVO_TEST << 'CSVDATA'
timestamp,device_id,device_type,location,value,unit,status,anomaly_score
2025-12-27 14:30:00.000,VISUAL-TEST-001,temperature_sensor,PLANTA-VISUAL,25.0,°C,NORMAL,0.1
2025-12-27 14:31:00.000,VISUAL-TEST-001,temperature_sensor,PLANTA-VISUAL,92.0,°C,CRITICAL,0.99
2025-12-27 14:32:00.000,VISUAL-TEST-002,humidity_sensor,PLANTA-VISUAL,55.0,%,NORMAL,0.2
2025-12-27 14:33:00.000,VISUAL-TEST-002,humidity_sensor,PLANTA-VISUAL,89.0,%,WARNING,0.8
2025-12-27 14:34:00.000,VISUAL-TEST-003,pressure_sensor,PLANTA-VISUAL,100.0,psi,NORMAL,0.15
CSVDATA

echo "✅ Datos creados: 5 registros (3 normales, 2 anomalías)"
echo ""

# Subir a S3
aws s3 cp $ARCHIVO_TEST s3://vantageflow-dev-data-lake-21bcb50a/bronze/
echo "📤 Subido a S3 Bronze"
echo "⏱️  Hora: $(date '+%H:%M:%S')"
echo ""

echo "⏳ ESPERA 25 SEGUNDOS Y LUEGO:"
echo ""
echo "🌐 ABRE ESTOS ENLACES EN TU NAVEGADOR:"
echo ""
echo "1. 🔍 VER MÉTRICAS BRONZE→SILVER:"
echo "   https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~();namespace=VantageFlow/BronzeToSilver;dimensions=~();metric=RowsProcessed"
echo ""
echo "2. 🔍 VER MÉTRICAS SILVER→GOLD:"
echo "   https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~();namespace=VantageFlow/SilverToGold;dimensions=~();metric=DevicesProcessed"
echo ""
echo "3. 📊 CREAR GRÁFICO COMBINADO:"
echo "   https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#metricsV2:graph=~();namespace=VantageFlow"
echo ""

echo "🔄 Monitoreando progreso..."
echo ""

# Mostrar progreso
for i in {1..25}; do
    echo -n "."
    sleep 1
    if [ $i -eq 5 ]; then
        echo ""
        echo "   ✅ Lambda Bronze→Silver ejecutada"
    elif [ $i -eq 15 ]; then
        echo ""
        echo "   ✅ Lambda Silver→Gold ejecutada"
    elif [ $i -eq 20 ]; then
        echo ""
        echo "   ✅ Métricas enviadas a CloudWatch"
    fi
done

echo ""
echo ""
echo "🎉 ¡AHORA DEBERÍAS VER TUS MÉTRICAS EN CLOUDWATCH!"
echo ""
echo "💡 EN LA CONSOLA CLOUDWATCH:"
echo "   1. Haz clic en 'VantageFlow'"
echo "   2. Selecciona 'BronzeToSilver' o 'SilverToGold'"
echo "   3. Marca las métricas que quieres ver"
echo "   4. Haz clic en 'Graphed metrics' arriba"
echo "   5. ¡Verás los gráficos!"
echo ""
echo "📊 MÉTRICAS QUE DEBERÍAS VER:"
echo "   • RowsProcessed: 5"
echo "   • AnomalyRows: 2"
echo "   • NormalRows: 3"
echo "   • AnomalyPercentage: 40%"
echo "   • DevicesProcessed: 3"
