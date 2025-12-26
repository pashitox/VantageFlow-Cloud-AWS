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
# 4. FUNCIÓN LAMBDA (ETL IOT)
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
    }
  }
}


############################################
# 5. PERMITIR QUE S3 INVOQUE LAMBDA
############################################
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_iot.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.vantageflow_data_lake.arn
}

############################################
# 6. TRIGGER AUTOMÁTICO S3 → LAMBDA
############################################
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.process_iot.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "bronze/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

############################################
# 7. OUTPUTS (VERIFICACIÓN)
############################################
output "lambda_name" {
  value = aws_lambda_function.process_iot.function_name
}

output "lambda_arn" {
  value = aws_lambda_function.process_iot.arn
}

output "lambda_console_url" {
  value = "https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/${aws_lambda_function.process_iot.function_name}"
}

output "pipeline_status" {
  value = "🚀 Pipeline S3 → Lambda → Silver ACTIVO"
}
