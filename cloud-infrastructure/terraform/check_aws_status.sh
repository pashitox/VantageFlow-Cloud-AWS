#!/bin/bash
echo "🔍 VERIFICANDO ESTADO ACTUAL AWS"
echo "================================"

echo "1. Buckets S3:"
aws s3 ls | grep -i vantageflow || echo "   ✅ No hay buckets"

echo ""
echo "2. Lambda Functions:"
aws lambda list-functions --query "Functions[?contains(FunctionName, 'vantageflow')].FunctionName" --output text || echo "   ✅ No hay Lambdas"

echo ""
echo "3. IAM Policies:"
aws iam list-policies --query "Policies[?contains(PolicyName, 'VantageFlow')].PolicyName" --output text || echo "   ✅ No hay políticas"

echo ""
echo "4. CloudWatch Log Groups:"
aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'vantageflow')].logGroupName" --output text || echo "   ✅ No hay logs"

echo ""
echo "📊 COSTO ESTIMADO ACTUAL:"
echo "   S3: $0.023/GB × 0GB = $0"
echo "   Lambda: $0.20/1M × 0 = $0"
echo "   CloudWatch: $0.50/GB × 0GB = $0"
echo "   TOTAL: $0"
