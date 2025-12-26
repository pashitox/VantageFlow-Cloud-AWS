# Configuración básica de Terraform para AWS
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # BACKEND PARA EQUIPO (opcional futuro)
  # backend "s3" {
  #   bucket = "vantageflow-terraform-state"
  #   key    = "terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Configurar proveedor AWS
provider "aws" {
  region = "us-east-1"
  
  # Tags por defecto para TODOS los recursos
  default_tags {
    tags = {
      Project     = "VantageFlow-Cloud"
      Environment = "Development"
      ManagedBy   = "Terraform"
      Owner       = "Data-Engineering-Team"
    }
  }
}

# VARIABLES (hacemos el código más flexible)
variable "project_name" {
  description = "Nombre del proyecto para naming de recursos"
  type        = string
  default     = "vantageflow"
}

variable "environment" {
  description = "Entorno de despliegue"
  type        = string
  default     = "dev"
}

# LOCALS (cálculos reutilizables)
locals {
  # Nombre de bucket válido: solo minúsculas, números, guiones
  bucket_name = "${var.project_name}-${var.environment}-data-lake-${random_id.bucket_suffix.hex}"
  
  # Estructura de carpetas para tu data lake
  data_lake_folders = ["bronze", "silver", "gold", "logs"]
}

# Sufijo aleatorio para nombre único de bucket
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# 1. BUCKET S3 PRINCIPAL - Data Lake
resource "aws_s3_bucket" "vantageflow_data_lake" {
  bucket = local.bucket_name
  
  # Prevención de eliminación accidental
  force_destroy = false
  
  tags = {
    Name        = "VantageFlow Data Lake"
    DataTier    = "All"
    CostCenter  = "Data-Engineering"
  }
}

# 2. VERSIONADO (para recuperación de datos)
resource "aws_s3_bucket_versioning" "data_lake_versioning" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 3. BLOQUEO DE ACCESO PÚBLICO (seguridad)
resource "aws_s3_bucket_public_access_block" "data_lake_block" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 4. ENCRIPCIÓN POR DEFECTO (seguridad + compliance)
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_encryption" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # Encriptación gratis con AWS-managed keys
    }
  }
}

# 5. POLÍTICA DE LIFECYCLE (optimización de costos)
resource "aws_s3_bucket_lifecycle_configuration" "data_lake_lifecycle" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id

  rule {
    id     = "move_to_glacier_after_90_days"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"  # Reduce costos 70% para datos antiguos
    }
  }
}

# 6. CREAR CARPETAS DE DATA LAKE AUTOMÁTICAMENTE
resource "aws_s3_object" "data_lake_folders" {
  for_each = toset(local.data_lake_folders)
  
  bucket = aws_s3_bucket.vantageflow_data_lake.id
  key    = "${each.value}/"
  source = "/dev/null"  # Truco para crear "folders" en S3
  
  depends_on = [aws_s3_bucket.vantageflow_data_lake]
}

# 7. BUCKET PARA LOGS (mejores prácticas)
resource "aws_s3_bucket" "vantageflow_logs" {
  bucket = "${var.project_name}-${var.environment}-logs-${random_id.bucket_suffix.hex}"
  
  force_destroy = false
  
  tags = {
    Name        = "VantageFlow Logs"
    DataTier    = "Logs"
    CostCenter  = "Infrastructure"
  }
}

# 8. HABILITAR LOGGING DEL BUCKET PRINCIPAL
resource "aws_s3_bucket_logging" "data_lake_logging" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id

  target_bucket = aws_s3_bucket.vantageflow_logs.id
  target_prefix = "s3-logs/"
}

# OUTPUTS (información útil después del deploy)
output "s3_bucket_name" {
  value       = aws_s3_bucket.vantageflow_data_lake.bucket
  description = "Nombre del bucket S3 principal (Data Lake)"
}

output "s3_logs_bucket_name" {
  value       = aws_s3_bucket.vantageflow_logs.bucket
  description = "Nombre del bucket para logs"
}

output "data_lake_folders" {
  value       = local.data_lake_folders
  description = "Estructura de carpetas creadas en el Data Lake"
}

output "s3_bucket_arn" {
  value       = aws_s3_bucket.vantageflow_data_lake.arn
  description = "ARN del bucket para políticas IAM"
}

output "next_steps" {
  value = <<-EOT
    🎉 ¡Infraestructura desplegada exitosamente!
    
    📊 RECURSOS CREADOS:
    1. Data Lake S3: ${aws_s3_bucket.vantageflow_data_lake.bucket}
    2. Bucket de Logs: ${aws_s3_bucket.vantageflow_logs.bucket}
    3. Carpetas: ${join(", ", local.data_lake_folders)}
    
    🚀 PRÓXIMOS PASOS:
    1. Subir datos: python3 data-pipeline/01_ingestion/s3_uploader.py
    2. Configurar IAM roles para Glue/Lambda
    3. Crear CloudWatch dashboard para monitoreo
    
    💡 COMANDOS ÚTILES:
    - Ver buckets: aws s3 ls
    - Listar carpetas: aws s3 ls s3://${aws_s3_bucket.vantageflow_data_lake.bucket}/
    - Subir archivo: aws s3 cp mi_archivo.csv s3://${aws_s3_bucket.vantageflow_data_lake.bucket}/bronze/
  EOT
}