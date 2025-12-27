.PHONY: help clean ingest monitor test verify install-deps run-all

help:
	@echo "================================================================="
	@echo "🚀 COMANDOS DISPONIBLES PARA INGESTA DE DATOS IoT"
	@echo "================================================================="
	@echo ""
	@echo "  make help         - Muestra este mensaje de ayuda"
	@echo "  make install-deps - Instala dependencias Python (boto3, pandas, numpy)"
	@echo "  make clean        - Limpia todo para empezar fresco"
	@echo "  make test         - Prueba con un lote pequeño (50 registros)"
	@echo "  make ingest       - Ejecuta ingesta completa (3 lotes x 200 registros)"
	@echo "  make monitor      - Monitorea logs en tiempo real (30 segundos)"
	@echo "  make verify       - Verifica estado del pipeline"
	@echo "  make run-all      - Ejecuta TODO: clean → ingest → verify"
	@echo ""
	@echo "💡 Ejemplo rápido: make run-all"
	@echo "================================================================="

install-deps:
	@echo "📦 INSTALANDO DEPENDENCIAS PYTHON..."
	@echo "   Este paso ya lo hiciste en el entorno virtual"
	@echo "   ✅ Dependencias ya instaladas:"
	@echo "   • boto3  - AWS SDK para Python"
	@echo "   • pandas - Manipulación de datos"
	@echo "   • numpy  - Cálculos numéricos"
	@python3 -c "import boto3, pandas, numpy; print('   ✅ Todas las dependencias funcionan correctamente')"

clean:
	@echo "🧹 EJECUTANDO LIMPIEZA INICIAL..."
	@chmod +x clean_start.sh 2>/dev/null || true
	@./clean_start.sh
	@echo "✅ Limpieza completada - Listo para nueva ingesta"

ingest:
	@echo "================================================================="
	@echo "🚀 INICIANDO INGESTA PROFESIONAL"
	@echo "================================================================="
	@echo "Configuración:"
	@echo "   • Lotes: 3"
	@echo "   • Registros por lote: 200"
	@echo "   • Total estimado: 600 registros"
	@echo "================================================================="
	@python3 s3_data_ingestor.py --batches 3 --records 200

test:
	@echo "🧪 EJECUTANDO PRUEBA RÁPIDA"
	@echo "   • Lotes: 1"
	@echo "   • Registros por lote: 50"
	@echo "   • Total: 50 registros"
	@python3 s3_data_ingestor.py --batches 1 --records 50

monitor:
	@echo "🔍 MONITOREANDO PIPELINE EN TIEMPO REAL"
	@echo "Presiona Ctrl+C para detener en cualquier momento"
	@echo ""
	@echo "=== ÚLTIMOS LOGS (30 segundos) ==="
	@echo ""
	@echo "📊 LAMBDA BRONZE → SILVER:"
	@timeout 30 aws logs tail /aws/lambda/vantageflow-process-iot --follow 2>/dev/null || echo "   No hay logs recientes o timeout"
	@echo ""
	@echo "📊 LAMBDA SILVER → GOLD:"
	@timeout 30 aws logs tail /aws/lambda/vantageflow-silver-to-gold --follow 2>/dev/null || echo "   No hay logs recientes o timeout"

verify:
	@echo "📊 VERIFICANDO ESTADO COMPLETO DEL PIPELINE"
	@echo "============================================"
	@echo ""
	@echo "1. 📁 ARCHIVOS EN S3:"
	@echo "---------------------"
	@aws s3 ls s3://vantageflow-dev-data-lake-21bcb50a/ --recursive --human-readable 2>/dev/null | grep -v ".keep" | head -20 || echo "   No hay archivos o error"
	@echo ""
	@echo "2. ⚡ ESTADO DE LAMBDAS:"
	@echo "-----------------------"
	@echo -n "   • vantageflow-process-iot: "
	@aws lambda get-function --function-name vantageflow-process-iot --query "Configuration.State" --output text 2>/dev/null || echo "Error"
	@echo -n "   • vantageflow-silver-to-gold: "
	@aws lambda get-function --function-name vantageflow-silver-to-gold --query "Configuration.State" --output text 2>/dev/null || echo "Error"
	@echo ""
	@echo "3. 🔗 TRIGGERS ACTIVOS:"
	@echo "----------------------"
	@aws s3api get-bucket-notification-configuration --bucket vantageflow-dev-data-lake-21bcb50a --query "LambdaFunctionConfigurations[*].Id" --output text 2>/dev/null | tr '\t' '\n' | while read trigger; do echo "   • $trigger"; done || echo "   No se pudieron leer los triggers"
	@echo ""
	@echo "4. 📈 RESUMEN POR CAPA:"
	@echo "----------------------"
	@for layer in bronze silver gold anomalies; do \
		count=$$(aws s3 ls s3://vantageflow-dev-data-lake-21bcb50a/$$layer/ --recursive 2>/dev/null | grep -v ".keep" | wc -l); \
		echo "   • $${layer^^}: $$count archivos"; \
	done
	@echo "============================================"

run-all:
	@echo "🎯 EJECUTANDO PIPELINE COMPLETO AUTOMÁTICO"
	@echo "=========================================="
	@$(MAKE) clean
	@echo ""
	@$(MAKE) ingest
	@echo ""
	@$(MAKE) verify
	@echo ""
	@echo "✅ PIPELINE COMPLETO EJECUTADO EXITOSAMENTE"
	@echo "=========================================="
