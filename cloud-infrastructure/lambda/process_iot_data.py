import json
import boto3
import csv
import io
import logging
from datetime import datetime

# Configurar logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clientes AWS
s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

# Umbral para considerar un dato como anomalía
ANOMALY_THRESHOLD = 0.5

def lambda_handler(event, context):
    logger.info("=== VANTAGEFLOW LAMBDA (Bronze→Silver) ===")
    logger.debug(f"Evento recibido: {json.dumps(event, indent=2)}")
    
    # Métricas iniciales
    metrics_data = []
    start_time = datetime.now()
    
    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        
        logger.info(f"Procesando archivo: s3://{bucket}/{key}")

        if not key.endswith(".csv"):
            logger.warning("No es CSV, se ignora")
            return {"statusCode": 200}

        # Leer CSV desde S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj["Body"].read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(body))
        rows = list(reader)
        
        total_rows = len(rows)
        logger.info(f"Filas leídas: {total_rows}")
        
        # Métrica: Total de filas procesadas
        metrics_data.append({
            'MetricName': 'RowsProcessed',
            'Value': total_rows,
            'Unit': 'Count'
        })

        # Separar filas normales y anomalías
        normal_rows = []
        anomalies_rows = []
        
        for row in rows:
            try:
                score = float(row.get("anomaly_score", 0))
            except:
                score = 0
            if score > ANOMALY_THRESHOLD:
                anomalies_rows.append(row)
            else:
                normal_rows.append(row)

        normal_count = len(normal_rows)
        anomalies_count = len(anomalies_rows)
        
        logger.info(f"Filas normales: {normal_count} | Anomalías: {anomalies_count}")
        
        # Métricas: Distribución de datos
        metrics_data.append({
            'MetricName': 'NormalRows',
            'Value': normal_count,
            'Unit': 'Count'
        })
        metrics_data.append({
            'MetricName': 'AnomalyRows',
            'Value': anomalies_count,
            'Unit': 'Count'
        })
        
        # Calcular porcentaje de anomalías
        if total_rows > 0:
            anomaly_percentage = (anomalies_count / total_rows) * 100
            metrics_data.append({
                'MetricName': 'AnomalyPercentage',
                'Value': anomaly_percentage,
                'Unit': 'Percent'
            })
            logger.info(f"Porcentaje de anomalías: {anomaly_percentage:.2f}%")

        # Guardar datos normales en silver/
        silver_key = key.replace("bronze/", "silver/")
        write_csv_to_s3(bucket, silver_key, normal_rows, reader.fieldnames)
        logger.info(f"✅ Silver guardado: s3://{bucket}/{silver_key}")
        
        # Métrica: Archivo Silver creado
        metrics_data.append({
            'MetricName': 'SilverFilesCreated',
            'Value': 1,
            'Unit': 'Count'
        })

        # Guardar anomalías en anomalies/
        if anomalies_count > 0:
            anomalies_key = key.replace("bronze/", "anomalies/")
            write_csv_to_s3(bucket, anomalies_key, anomalies_rows, reader.fieldnames)
            logger.info(f"⚠️ Anomalías guardadas: s3://{bucket}/{anomalies_key}")
            
            # Métrica: Archivo Anomalías creado
            metrics_data.append({
                'MetricName': 'AnomalyFilesCreated',
                'Value': 1,
                'Unit': 'Count'
            })

        # Calcular tiempo de procesamiento
        processing_time = (datetime.now() - start_time).total_seconds() * 1000  # ms
        
        # Métricas de performance
        metrics_data.append({
            'MetricName': 'ProcessingTime',
            'Value': processing_time,
            'Unit': 'Milliseconds'
        })
        
        if total_rows > 0:
            rows_per_second = total_rows / (processing_time / 1000)
            metrics_data.append({
                'MetricName': 'RowsPerSecond',
                'Value': rows_per_second,
                'Unit': 'Count/Second'
            })

        # Enviar métricas a CloudWatch
        if metrics_data:
            try:
                cloudwatch.put_metric_data(
                    Namespace='VantageFlow/BronzeToSilver',
                    MetricData=metrics_data
                )
                logger.info(f"📊 {len(metrics_data)} métricas enviadas a CloudWatch")
            except Exception as e:
                logger.error(f"Error enviando métricas a CloudWatch: {str(e)}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "archivo": key,
                "filas_totales": total_rows,
                "filas_silver": normal_count,
                "filas_anomalies": anomalies_count,
                "anomaly_percentage": anomaly_percentage if total_rows > 0 else 0,
                "processing_time_ms": processing_time,
                "silver_key": silver_key,
                "anomalies_key": anomalies_key if anomalies_count > 0 else None
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento: {str(e)}")
        
        # Métrica de error
        try:
            cloudwatch.put_metric_data(
                Namespace='VantageFlow/BronzeToSilver',
                MetricData=[{
                    'MetricName': 'ProcessingErrors',
                    'Value': 1,
                    'Unit': 'Count'
                }]
            )
        except:
            pass
            
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def write_csv_to_s3(bucket, key, rows, fieldnames):
    if not rows:
        # Crear archivo vacío si no hay filas
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
    else:
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_buffer.getvalue()
    )