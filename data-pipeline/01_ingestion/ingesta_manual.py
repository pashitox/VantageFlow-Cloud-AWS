#!/usr/bin/env python3
"""
INGESTA MANUAL SUPER SIMPLE - Sin complicaciones
"""
import boto3
from datetime import datetime
import random
import csv
import io
import sys
import time

def main():
    print("=" * 60)
    print("🚀 INGESTA MANUAL DE DATOS IoT")
    print("=" * 60)
    
    # Configuración
    BUCKET = "vantageflow-dev-data-lake-21bcb50a"
    
    try:
        # 1. Conectar a S3
        s3 = boto3.client('s3')
        print("✅ Conectado a AWS S3")
    except Exception as e:
        print(f"❌ Error conectando a AWS: {e}")
        print("💡 Verifica: AWS credentials configuradas?")
        sys.exit(1)
    
    # 2. Generar y subir 3 lotes
    for batch in [1, 2, 3]:
        print(f"\n�� LOTE {batch}/3")
        print("-" * 40)
        
        # Crear datos manualmente (50 registros por lote)
        devices = [
            {"id": "FAB-TEM-001", "type": "temperature_sensor", "unit": "°C", "base": 25.0},
            {"id": "FAB-HUM-001", "type": "humidity_sensor", "unit": "%", "base": 50.0},
            {"id": "FAB-PRS-001", "type": "pressure_sensor", "unit": "psi", "base": 100.0},
        ]
        
        # Generar CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "device_id", "device_type", "location", "value", "unit", "status", "anomaly_score"])
        
        record_count = 0
        for i in range(50):  # 50 registros por lote
            device = random.choice(devices)
            
            # Valor base con variación
            value = device["base"] + random.uniform(-10, 15)
            
            # Anomalía (10% probabilidad)
            anomaly_score = random.random()
            if anomaly_score > 0.9:
                status = "CRITICAL"
                value *= 1.8
            elif anomaly_score > 0.7:
                status = "WARNING"
                value *= 1.4
            else:
                status = "NORMAL"
            
            # Escribir fila
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                device["id"],
                device["type"],
                "FABRICA-A",
                round(value, 3),
                device["unit"],
                status,
                round(anomaly_score, 3)
            ])
            record_count += 1
        
        # 3. Subir a S3
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"bronze/lote_{batch}_{timestamp}.csv"
        
        try:
            s3.put_object(
                Bucket=BUCKET,
                Key=s3_key,
                Body=output.getvalue(),
                ContentType='text/csv'
            )
            print(f"✅ Subido a S3: {s3_key}")
            print(f"   📊 {record_count} registros | Último valor: {value:.1f}{device['unit']}")
            
            # 4. Pequeña pausa para que el pipeline procese
            if batch < 3:
                print("⏳ Esperando 10 segundos para procesamiento...")
                time.sleep(10)
                
        except Exception as e:
            print(f"❌ Error subiendo a S3: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 INGESTA COMPLETADA")
    print("=" * 60)
    
    # 5. Verificar resultados
    print("\n🔍 VERIFICANDO RESULTADOS:")
    print("-" * 40)
    
    for layer in ["bronze", "silver", "gold", "anomalies"]:
        try:
            response = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{layer}/")
            files = [obj for obj in response.get('Contents', []) 
                    if not obj['Key'].endswith('.keep')]
            print(f"   • {layer.upper():10} → {len(files):2} archivos")
            
            # Mostrar último archivo
            if files:
                last_file = sorted(files, key=lambda x: x['LastModified'])[-1]
                size_kb = last_file['Size'] / 1024
                name = last_file['Key'].split('/')[-1][:25]
                print(f"        Último: {name} ({size_kb:.1f} KB)")
                
        except Exception as e:
            print(f"   • {layer.upper():10} → Error: {e}")
    
    print("\n💡 COMANDOS PARA VERIFICAR MANUALMENTE:")
    print(f"   aws s3 ls s3://{BUCKET}/bronze/ --recursive")
    print(f"   aws s3 ls s3://{BUCKET}/gold/ --recursive")

if __name__ == "__main__":
    main()
