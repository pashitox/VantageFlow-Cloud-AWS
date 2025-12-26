# 1. IAM Role para Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "vantageflow-lambda-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# 2. Política básica para S3
resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

# 3. Política para CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 4. Lambda Function CON ZIP
resource "aws_lambda_function" "process_iot" {
  function_name = "vantageflow-process-iot"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "process_iot_data.lambda_handler"
  runtime       = "python3.12"
  timeout       = 10
  
  # Usar archivo ZIP (¡IMPORTANTE!)
  filename         = "${path.module}/../lambda/process_iot.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/process_iot.zip")
  
  environment {
    variables = {
      PROJECT = "VantageFlow"
    }
  }
}

# 5. Outputs para verificar
output "lambda_name" {
  value = aws_lambda_function.process_iot.function_name
}

output "lambda_arn" {
  value = aws_lambda_function.process_iot.arn
}

output "lambda_url" {
  value = "https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/${aws_lambda_function.process_iot.function_name}"
}

# ============================================
# TRIGGER AUTOMÁTICO S3 -> LAMBDA
# ============================================

# Permiso para que S3 pueda invocar Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_iot.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.vantageflow_data_lake.arn
}

# Configurar notificación del bucket S3
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.process_iot.arn
    events              = ["s3:ObjectCreated:*"]  # Cuando se crea archivo
    filter_prefix       = "bronze/"              # Solo en carpeta bronze
    filter_suffix       = ".csv"                 # Solo archivos CSV
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

output "pipeline_status" {
  value = "🚀 Pipeline S3→Lambda CONFIGURADO. ¡Ahora es automático!"
}
