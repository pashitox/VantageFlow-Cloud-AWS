#!/bin/bash
echo "🔥 DESTRUYENDO TODA LA INFRAESTRUCTURA AWS"
echo "=========================================="
echo ""
echo "⚠️  ADVERTENCIA: Esto eliminará PERMANENTEMENTE:"
echo "   • Bucket S3 completo"
echo "   • Lambda functions"
echo "   • IAM policies"
echo "   • CloudWatch logs"
echo "   • TODOS los recursos del proyecto"
echo ""
read -p "¿Estás seguro? (si/NO): " confirm

if [[ "$confirm" != "si" ]]; then
    echo "❌ Operación cancelada"
    exit 1
fi

echo ""
echo "1️⃣ DESTRUYENDO CON TERRAFORM..."
echo "================================"
cd /home/pashitox/Documentos/VantageFlow-Cloud-AWS/cloud-infrastructure/terraform

if [ -f "terraform.tfstate" ]; then
    echo "✅ Estado de Terraform encontrado"
    terraform destroy -auto-approve
    echo "✅ Terraform destroy completado"
else
    echo "⚠️  No hay estado de Terraform, destruyendo manualmente..."
fi

echo ""
echo "2️⃣ ELIMINANDO BUCKET S3..."
echo "=========================="
BUCKET="vantageflow-dev-data-lake-21bcb50a"

# Verificar si el bucket existe
if aws s3 ls "s3://$BUCKET" 2>/dev/null; then
    echo "✅ Bucket encontrado: $BUCKET"
    
    # Vaciar bucket primero (requerido antes de eliminar)
    echo "   Vacíando bucket..."
    aws s3 rm "s3://$BUCKET" --recursive --quiet
    
    # Eliminar bucket
    echo "   Eliminando bucket..."
    aws s3 rb "s3://$BUCKET" --force
    echo "✅ Bucket eliminado"
else
    echo "⚠️  Bucket no encontrado o ya eliminado"
fi

echo ""
echo "3️⃣ ELIMINANDO LAMBDA FUNCTIONS..."
echo "=================================="

# Listar y eliminar Lambdas
LAMBDAS=$(aws lambda list-functions --query "Functions[?contains(FunctionName, 'vantageflow')].FunctionName" --output text)

if [ -n "$LAMBDAS" ]; then
    echo "Encontradas Lambdas:"
    for lambda in $LAMBDAS; do
        echo "   • Eliminando: $lambda"
        aws lambda delete-function --function-name "$lambda"
    done
    echo "✅ Lambdas eliminadas"
else
    echo "⚠️  No se encontraron Lambdas"
fi

echo ""
echo "4️⃣ ELIMINANDO IAM POLICIES..."
echo "=============================="

# Eliminar política personalizada
POLICY_NAME="VantageFlowCloudWatchMetrics"
POLICY_ARN="arn:aws:iam::165518479619:policy/$POLICY_NAME"

if aws iam get-policy --policy-arn "$POLICY_ARN" 2>/dev/null; then
    echo "✅ Política encontrada: $POLICY_NAME"
    
    # Primero desvincular del rol
    echo "   Desvinculando del rol..."
    aws iam detach-role-policy --role-name vantageflow-lambda-role --policy-arn "$POLICY_ARN" 2>/dev/null || true
    
    # Eliminar versiones de la política
    echo "   Eliminando versiones de política..."
    versions=$(aws iam list-policy-versions --policy-arn "$POLICY_ARN" --query "Versions[?VersionId != 'v1'].VersionId" --output text)
    for version in $versions; do
        aws iam delete-policy-version --policy-arn "$POLICY_ARN" --version-id "$version"
    done
    
    # Eliminar política
    aws iam delete-policy --policy-arn "$POLICY_ARN"
    echo "✅ Política eliminada"
else
    echo "⚠️  Política no encontrada"
fi

echo ""
echo "5️⃣ ELIMINANDO CLOUDWATCH LOG GROUPS..."
echo "======================================="

LOG_GROUPS=$(aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'vantageflow')].logGroupName" --output text)

if [ -n "$LOG_GROUPS" ]; then
    echo "Encontrados Log Groups:"
    for log_group in $LOG_GROUPS; do
        echo "   • Eliminando: $log_group"
        aws logs delete-log-group --log-group-name "$log_group"
    done
    echo "✅ Log Groups eliminados"
else
    echo "⚠️  No se encontraron Log Groups"
fi

echo ""
echo "6️⃣ VERIFICANDO QUE TODO ESTÉ ELIMINADO..."
echo "=========================================="

echo "📋 Estado final:"
echo ""

# Verificar S3
echo "🔍 Verificando S3..."
aws s3 ls "s3://$BUCKET" 2>/dev/null && echo "❌ Bucket todavía existe" || echo "✅ Bucket eliminado"

# Verificar Lambdas
echo "🔍 Verificando Lambdas..."
aws lambda list-functions --query "Functions[?contains(FunctionName, 'vantageflow')].FunctionName" --output text | \
    if [ -z "$(cat)" ]; then echo "✅ Lambdas eliminadas"; else echo "❌ Todavía hay Lambdas"; fi

# Verificar IAM Policy
echo "🔍 Verificando IAM Policy..."
aws iam list-policies --query "Policies[?contains(PolicyName, 'VantageFlow')].PolicyName" --output text | \
    if [ -z "$(cat)" ]; then echo "✅ Política eliminada"; else echo "❌ Política todavía existe"; fi

# Verificar CloudWatch Logs
echo "🔍 Verificando CloudWatch Logs..."
aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'vantageflow')].logGroupName" --output text | \
    if [ -z "$(cat)" ]; then echo "✅ Logs eliminados"; else echo "❌ Logs todavía existen"; fi

echo ""
echo "🎉 ¡TODA LA INFRAESTRUCTURA AWS HA SIDO ELIMINADA!"
echo ""
echo "�� RESUMEN DE AHORRO DE COSTOS:"
echo "   • S3 Storage: $0.023/GB → ELIMINADO"
echo "   • Lambda: $0.20/1M invocaciones → ELIMINADO"
echo "   • CloudWatch: $0.50/GB logs → ELIMINADO"
echo "   • Total mensual estimado: $0 (ahorro 100%)"
echo ""
echo "�� Para recrear la infraestructura:"
echo "   cd cloud-infrastructure/terraform && terraform apply"
echo ""
echo "⚠️  Recuerda:"
echo "   1. AWS puede tardar hasta 24h en reflejar todos los cambios de facturación"
echo "   2. Los logs pueden permanecer en CloudWatch por unas horas"
echo "   3. Verifica tu cuenta AWS en 1-2 días para confirmar"
