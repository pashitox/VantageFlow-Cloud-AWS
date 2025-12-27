#!/bin/bash
echo "📊 VISUALIZADOR DE MÉTRICAS CLOUDWATCH - CLI"
echo "============================================"
echo ""

while true; do
    clear
    
    echo "⏰ Última actualización: $(date '+%H:%M:%S')"
    echo ""
    
    # Mostrar namespaces VantageFlow
    echo "🔍 BUSCANDO NAMESPACES VantageFlow..."
    echo ""
    
    namespaces=$(aws cloudwatch list-metrics --query "Metrics[?starts_with(Namespace, 'VantageFlow')].Namespace" --output text 2>/dev/null | tr '\t' '\n' | sort -u)
    
    if [ -z "$namespaces" ]; then
        echo "⚠️  No se encontraron namespaces VantageFlow"
        echo "   Espera 1-2 minutos después de ejecutar el pipeline"
    else
        echo "✅ NAMESPACES ENCONTRADOS:"
        echo "$namespaces"
        echo ""
        
        # Para cada namespace, mostrar métricas
        for ns in $namespaces; do
            echo "📊 $ns"
            echo "────────────────────────────"
            
            # Obtener métricas
            metricas=$(aws cloudwatch list-metrics --namespace "$ns" --query "Metrics[*].MetricName" --output text 2>/dev/null)
            
            if [ -n "$metricas" ]; then
                # Contar y mostrar
                count=$(echo $metricas | wc -w)
                echo "Métricas: $count"
                
                # Mostrar primeras 5
                echo "Primeras 5 métricas:"
                echo "$metricas" | tr ' ' '\n' | head -5 | while read metrica; do
                    echo "  • $metrica"
                done
                
                if [ $count -gt 5 ]; then
                    echo "  ... y $((count-5)) más"
                fi
            else
                echo "  (Sin métricas aún)"
            fi
            echo ""
        done
        
        # Intentar obtener datos de una métrica específica
        echo "📈 DATOS DE EJEMPLO (RowsProcessed - últimos 15 min):"
        echo "────────────────────────────────────────────────────"
        
        for ns in $namespaces; do
            echo "  $ns:"
            # Usar una consulta más simple que no requiera GetMetricStatistics
            metricas_count=$(aws cloudwatch list-metrics --namespace "$ns" --metric-name "RowsProcessed" --query "length(Metrics)" 2>/dev/null)
            
            if [ "$metricas_count" -gt "0" ]; then
                echo "    ✅ Métrica 'RowsProcessed' presente"
            else
                echo "    ⚠️  Métrica no disponible aún"
            fi
        done
    fi
    
    echo ""
    echo "�� Actualizando en 30 segundos... (Ctrl+C para salir)"
    echo "🌐 Para ver gráficos: https://us-east-1.console.aws.amazon.com/cloudwatch/home#metricsV2"
    sleep 30
done
