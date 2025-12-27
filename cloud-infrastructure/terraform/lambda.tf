############################################
# 1. IAM ROLE PARA LAMBDA
############################################
resource "aws_iam_role" "lambda_exec_role" {
  name = "vantageflow-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

############################################
# 2. PERMISOS S3 (LECTURA + ESCRITURA)
############################################
resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

############################################
# 3. PERMISOS CLOUDWATCH LOGS
############################################
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

############################################
# 4. FUNCIÓN LAMBDA (BRONZE → SILVER)
############################################
resource "aws_lambda_function" "process_iot" {
  function_name = "vantageflow-process-iot"
  handler       = "process_iot_data.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_exec_role.arn

  filename         = "../lambda/process_iot.zip"
  source_code_hash = filebase64sha256("../lambda/process_iot.zip")

  memory_size = 512
  timeout     = 60

  environment {
    variables = {
      STAGE = "dev"
      ANOMALY_THRESHOLD = "0.5"
    }
  }
}

############################################
# 5. FUNCIÓN LAMBDA (SILVER → GOLD)
############################################
resource "aws_lambda_function" "silver_to_gold" {
  function_name = "vantageflow-silver-to-gold"
  handler       = "process_silver_to_gold.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_exec_role.arn

  filename         = "../lambda/process_silver_to_gold.zip"
  source_code_hash = filebase64sha256("../lambda/process_silver_to_gold.zip")

  memory_size = 512
  timeout     = 120  # Más tiempo para procesamiento Gold

  environment {
    variables = {
      STAGE = "dev"
      LOG_LEVEL = "INFO"
    }
  }
}

############################################
# 6. PERMITIR QUE S3 INVOQUE LAMBDA BRONZE
############################################
resource "aws_lambda_permission" "allow_s3_bronze" {
  statement_id  = "AllowS3InvokeBronze"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_iot.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.vantageflow_data_lake.arn
}

############################################
# 7. PERMITIR QUE S3 INVOQUE LAMBDA SILVER
############################################
resource "aws_lambda_permission" "allow_s3_silver" {
  statement_id  = "AllowS3InvokeSilver"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.silver_to_gold.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.vantageflow_data_lake.arn
}

############################################
# 8. TRIGGER AUTOMÁTICO BRONZE → LAMBDA
############################################
resource "aws_s3_bucket_notification" "bronze_notification" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.process_iot.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "bronze/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3_bronze]
}

############################################
# 9. TRIGGER AUTOMÁTICO SILVER → LAMBDA GOLD
############################################
resource "aws_s3_bucket_notification" "silver_notification" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.silver_to_gold.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "silver/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3_silver]
}

############################################
# 10. OUTPUTS (VERIFICACIÓN)
############################################
output "lambda_bronze_name" {
  value = aws_lambda_function.process_iot.function_name
}

output "lambda_gold_name" {
  value = aws_lambda_function.silver_to_gold.function_name
}

output "lambda_bronze_arn" {
  value = aws_lambda_function.process_iot.arn
}

output "lambda_gold_arn" {
  value = aws_lambda_function.silver_to_gold.arn
}

output "pipeline_bronze_to_silver_status" {
  value = "✅ Pipeline BRONZE → SILVER ACTIVO"
}

output "pipeline_silver_to_gold_status" {
  value = "✅ Pipeline SILVER → GOLD ACTIVO"
}

output "bucket_name" {
  value = aws_s3_bucket.vantageflow_data_lake.bucket
}

output "full_pipeline_status" {
  value = "🚀 Pipeline completo: S3(bronze) → Lambda → S3(silver) → Lambda → S3(gold)"
}

output "verification_commands" {
  value = <<-EOT
  Para verificar el funcionamiento:
  1. Sube un archivo a bronze/: aws s3 cp mi_archivo.csv s3://${aws_s3_bucket.vantageflow_data_lake.bucket}/bronze/
  2. Revisa silver/: aws s3 ls s3://${aws_s3_bucket.vantageflow_data_lake.bucket}/silver/
  3. Revisa gold/: aws s3 ls s3://${aws_s3_bucket.vantageflow_data_lake.bucket}/gold/
  4. Verifica logs en CloudWatch
  EOT
}