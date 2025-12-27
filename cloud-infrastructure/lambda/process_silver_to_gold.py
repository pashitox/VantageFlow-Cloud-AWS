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

def lambda_handler(event, context):
    logger.info("🚀 Lambda Gold (Silver→Gold) iniciada")
    
    # Métricas iniciales
    metrics_data = []
    start_time = datetime.now()
    
    try:
        # Obtener información del archivo
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        silver_key = record['s3']['object']['key']
        
        logger.info(f"Procesando archivo Silver: {silver_key}")
        
        # Solo procesar CSV en silver/
        if not silver_key.startswith('silver/') or not silver_key.endswith('.csv'):
            logger.warning("No es CSV en silver/, se ignora")
            return {'statusCode': 200}
        
        # Leer CSV desde S3
        response = s3.get_object(Bucket=bucket, Key=silver_key)
        content = response['Body'].read().decode('utf-8')
        
        # Procesar CSV
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        
        total_rows = len(rows)
        
        if not rows:
            logger.warning("Archivo CSV vacío")
            return {'statusCode': 200}
        
        logger.info(f"Filas a procesar: {total_rows}")
        
        # Métrica: Total de filas procesadas
        metrics_data.append({
            'MetricName': 'RowsProcessed',
            'Value': total_rows,
            'Unit': 'Count'
        })
        
        # --- AGREGACIÓN POR device_id ---
        device_stats = {}
        total_anomalies = 0
        
        for row in rows:
            device_id = row.get('device_id', 'unknown')
            
            if device_id not in device_stats:
                device_stats[device_id] = {
                    'count': 0,
                    'total_value': 0.0,
                    'min_value': float('inf'),
                    'max_value': float('-inf'),
                    'anomaly_count': 0
                }
            
            try:
                value = float(row.get('value', 0))
                anomaly_score = float(row.get('anomaly_score', 0))
            except ValueError:
                logger.warning(f"Fila con datos inválidos: {row}")
                continue
            
            # Actualizar estadísticas
            stats = device_stats[device_id]
            stats['count'] += 1
            stats['total_value'] += value
            stats['min_value'] = min(stats['min_value'], value)
            stats['max_value'] = max(stats['max_value'], value)
            
            # Contar anomalías (score > 0.5)
            if anomaly_score > 0.5:
                stats['anomaly_count'] += 1
                total_anomalies += 1
        
        # Métricas por dispositivo
        devices_processed = len(device_stats)
        metrics_data.append({
            'MetricName': 'DevicesProcessed',
            'Value': devices_processed,
            'Unit': 'Count'
        })
        metrics_data.append({
            'MetricName': 'TotalAnomalies',
            'Value': total_anomalies,
            'Unit': 'Count'
        })
        
        if total_rows > 0:
            anomaly_percentage = (total_anomalies / total_rows) * 100
            metrics_data.append({
                'MetricName': 'AnomalyPercentage',
                'Value': anomaly_percentage,
                'Unit': 'Percent'
            })
        
        logger.info(f"📊 Dispositivos procesados: {devices_processed}")
        logger.info(f"⚠️  Anomalías totales: {total_anomalies}")
        
        # Crear archivo Gold
        output = io.StringIO()
        fieldnames = ['device_id', 'total_readings', 'avg_value', 'min_value', 
                     'max_value', 'anomaly_count', 'anomaly_percentage']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for device_id, stats in device_stats.items():
            if stats['count'] > 0:
                avg_value = stats['total_value'] / stats['count']
                device_anomaly_percentage = (stats['anomaly_count'] / stats['count']) * 100
                
                writer.writerow({
                    'device_id': device_id,
                    'total_readings': stats['count'],
                    'avg_value': round(avg_value, 3),
                    'min_value': round(stats['min_value'], 3),
                    'max_value': round(stats['max_value'], 3),
                    'anomaly_count': stats['anomaly_count'],
                    'anomaly_percentage': round(device_anomaly_percentage, 2)
                })
        
        # Guardar en Gold
        gold_key = silver_key.replace('silver/', 'gold/')
        gold_content = output.getvalue()
        
        s3.put_object(
            Bucket=bucket,
            Key=gold_key,
            Body=gold_content,
            ContentType='text/csv'
        )
        
        # Métricas de salida
        gold_size_kb = len(gold_content.encode('utf-8')) / 1024
        metrics_data.append({
            'MetricName': 'GoldFilesCreated',
            'Value': 1,
            'Unit': 'Count'
        })
        metrics_data.append({
            'MetricName': 'GoldFileSizeKB',
            'Value': gold_size_kb,
            'Unit': 'Kilobytes'
        })
        
        logger.info(f"✅ Gold creado: {gold_key}")
        logger.info(f"📄 Tamaño del archivo Gold: {gold_size_kb:.2f} KB")
        
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
                    Namespace='VantageFlow/SilverToGold',
                    MetricData=metrics_data
                )
                logger.info(f"📊 {len(metrics_data)} métricas enviadas a CloudWatch")
            except Exception as e:
                logger.error(f"Error enviando métricas a CloudWatch: {str(e)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Gold procesado correctamente',
                'devices_processed': devices_processed,
                'total_rows': total_rows,
                'total_anomalies': total_anomalies,
                'gold_file': gold_key,
                'processing_time_ms': processing_time,
                'gold_file_size_kb': gold_size_kb
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error en Lambda Gold: {str(e)}")
        
        # Métrica de error
        try:
            cloudwatch.put_metric_data(
                Namespace='VantageFlow/SilverToGold',
                MetricData=[{
                    'MetricName': 'ProcessingErrors',
                    'Value': 1,
                    'Unit': 'Count'
                }]
            )
        except:
            pass
            
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }