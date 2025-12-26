import json
import boto3

def lambda_handler(event, context):
    print("=== VANTAGEFLOW LAMBDA INICIADA ===")
    
    # Log del evento recibido
    print("Evento recibido:", json.dumps(event, indent=2))
    
    # Procesar cada archivo que llegó a S3
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        print(f"📥 Nuevo archivo en S3:")
        print(f"   Bucket: {bucket}")
        print(f"   Archivo: {key}")
        
        # Aquí iría el procesamiento real
        # Por ahora solo registramos
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Procesamiento iniciado',
                'file': key,
                'bucket': bucket
            })
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps('No hay datos para procesar')
    }
