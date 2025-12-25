# Configuración básica de Terraform para AWS
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configurar proveedor AWS (usa tus credenciales CLI)
provider "aws" {
  region = "us-east-1"
}

# 1. CREAR BUCKET S3 ÚNICO - Tu Data Lake principal
resource "aws_s3_bucket" "vantageflow_data_lake" {
  bucket = "vantageflow-data-lake-${replace(timestamp(), ":", "")}"
  
  tags = {
    Project     = "VantageFlow Cloud"
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
  
  # Evitar colisiones de nombre
  lifecycle {
    ignore_changes = [bucket]
  }
}

# 2. HABILITAR VERSIONADO (mejores prácticas)
resource "aws_s3_bucket_versioning" "data_lake_versioning" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

# 3. BLOQUEAR ACCESO PÚBLICO (seguridad por defecto)
resource "aws_s3_bucket_public_access_block" "data_lake_block" {
  bucket = aws_s3_bucket.vantageflow_data_lake.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Mostrar nombre del bucket creado
output "s3_bucket_name" {
  value = aws_s3_bucket.vantageflow_data_lake.bucket
  description = "Nombre del bucket S3 creado para VantageFlow Cloud"
}