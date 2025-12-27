import json
import boto3
import csv
import io
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    logger.info("🚀 Lambda Gold iniciada")
    
    try:
        # Obtener información del archivo
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        silver_key = record['s3']['object']['key']
        
        logger.info(f"Procesando archivo Silver: {silver_key}")
        
        # Solo procesar CSV en silver/
        if not silver_key.startswith('silver/') or not silver_key.endswith('.csv'):
            return {'statusCode': 200}
        
        # Leer CSV desde S3
        response = s3.get_object(Bucket=bucket, Key=silver_key)
        content = response['Body'].read().decode('utf-8')
        
        # Procesar CSV
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        
        if not rows:
            logger.warning("Archivo CSV vacío")
            return {'statusCode': 200}
        
        # --- AGREGACIÓN POR device_id (CORREGIDO) ---
        device_stats = {}
        
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
        
        # Crear archivo Gold
        output = io.StringIO()
        fieldnames = ['device_id', 'total_readings', 'avg_value', 'min_value', 
                     'max_value', 'anomaly_count', 'anomaly_percentage']
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for device_id, stats in device_stats.items():
            if stats['count'] > 0:
                avg_value = stats['total_value'] / stats['count']
                anomaly_percentage = (stats['anomaly_count'] / stats['count']) * 100
                
                writer.writerow({
                    'device_id': device_id,
                    'total_readings': stats['count'],
                    'avg_value': round(avg_value, 3),
                    'min_value': round(stats['min_value'], 3),
                    'max_value': round(stats['max_value'], 3),
                    'anomaly_count': stats['anomaly_count'],
                    'anomaly_percentage': round(anomaly_percentage, 2)
                })
        
        # Guardar en Gold
        gold_key = silver_key.replace('silver/', 'gold/')
        s3.put_object(
            Bucket=bucket,
            Key=gold_key,
            Body=output.getvalue(),
            ContentType='text/csv'
        )
        
        logger.info(f"✅ Gold creado: {gold_key}")
        logger.info(f"📊 Dispositivos procesados: {len(device_stats)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Gold procesado correctamente',
                'devices_processed': len(device_stats),
                'gold_file': gold_key
            })
        }
        
    except Exception as e:
        logger.error(f"❌ Error en Lambda Gold: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
