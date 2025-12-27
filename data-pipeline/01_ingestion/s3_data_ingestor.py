# /home/pashitox/Documentos/VantageFlow-Cloud-AWS/data-pipeline/01_ingestion/s3_data_ingestor.py
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
import os
from pathlib import Path

class IoTDataIngestor:
    def __init__(self, bucket_name="vantageflow-dev-data-lake-21bcb50a"):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.local_raw_dir = Path("/home/pashitox/Documentos/VantageFlow-Cloud-AWS/data/raw")
        self.local_processed_dir = Path("/home/pashitox/Documentos/VantageFlow-Cloud-AWS/data/processed")
        
        # Crear directorios locales si no existen
        self.local_raw_dir.mkdir(parents=True, exist_ok=True)
        self.local_processed_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_iot_data(self, num_records=1000, num_devices=5):
        """Genera datos IoT realistas con la estructura especificada"""
        
        device_types = ['temperature_sensor', 'humidity_sensor', 'pressure_sensor', 
                       'vibration_sensor', 'energy_meter']
        locations = ['FABRICA-A', 'FABRICA-B', 'ALMACEN-1', 'LINEA-PRODUCCION', 'SALA-SERVIDORES']
        units = ['°C', '%', 'psi', 'g', 'kW']
        status_options = ['NORMAL', 'WARNING', 'CRITICAL']
        
        devices = []
        for i in range(num_devices):
            device_type = random.choice(device_types)
            devices.append({
                'device_id': f"{device_type[:3].upper()}-{locations[i % len(locations)][:3]}-{str(i+1).zfill(3)}",
                'device_type': device_type,
                'location': locations[i % len(locations)],
                'unit': units[device_types.index(device_type) % len(units)],
                'base_value': {
                    'temperature_sensor': 25.0,
                    'humidity_sensor': 50.0,
                    'pressure_sensor': 100.0,
                    'vibration_sensor': 0.5,
                    'energy_meter': 2.5
                }[device_type]
            })
        
        data = []
        base_time = datetime.now() - timedelta(days=7)
        
        for i in range(num_records):
            device = random.choice(devices)
            
            # Generar timestamp incremental
            timestamp = base_time + timedelta(seconds=i * 30)  # Cada 30 segundos
            
            # Generar valor base con variación
            base_val = device['base_value']
            variation = np.random.normal(0, base_val * 0.2)  # 20% de variación
            value = base_val + variation
            
            # Generar anomalías (5% de probabilidad)
            is_anomaly = np.random.random() < 0.05
            anomaly_score = np.random.random()  # Score entre 0-1
            
            if is_anomaly:
                # Aumentar valor para anomalías
                value *= np.random.uniform(1.5, 3.0)
                anomaly_score = np.random.uniform(0.7, 1.0)
                status = random.choice(['WARNING', 'CRITICAL'])
            else:
                status = 'NORMAL'
            
            # Ajustar anomalía score para valores extremos
            if value > base_val * 2:
                anomaly_score = max(anomaly_score, 0.8)
            
            record = {
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'device_id': device['device_id'],
                'device_type': device['device_type'],
                'location': device['location'],
                'value': round(value, 3),
                'unit': device['unit'],
                'status': status,
                'anomaly_score': round(anomaly_score, 3)
            }
            
            data.append(record)
        
        return pd.DataFrame(data)
    
    def save_locally(self, df, batch_number=1):
        """Guarda datos localmente como respaldo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Guardar en raw
        raw_filename = self.local_raw_dir / f'iot_batch_{batch_number}_{timestamp}.csv'
        df.to_csv(raw_filename, index=False)
        print(f"✅ Datos guardados localmente (raw): {raw_filename}")
        
        # Guardar en processed (simplificado)
        processed_filename = self.local_processed_dir / f'processed_batch_{batch_number}_{timestamp}.csv'
        
        # Simular procesamiento simple
        processed_df = df.copy()
        processed_df['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        processed_df.to_csv(processed_filename, index=False)
        print(f"✅ Datos guardados localmente (processed): {processed_filename}")
        
        return raw_filename, processed_filename
    
    def upload_to_s3(self, df, batch_number=1):
        """Sube datos a S3 bucket (bronze layer)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"bronze/iot_batch_{batch_number}_{timestamp}.csv"
        
        # Convertir DataFrame a CSV en memoria
        csv_buffer = df.to_csv(index=False)
        
        try:
            # Subir a S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=csv_buffer,
                ContentType='text/csv'
            )
            
            print(f"🚀 Datos subidos a S3: s3://{self.bucket_name}/{s3_key}")
            print(f"   📊 {len(df)} registros | {df['device_id'].nunique()} dispositivos")
            
            return s3_key
            
        except Exception as e:
            print(f"❌ Error subiendo a S3: {str(e)}")
            return None
    
    def monitor_pipeline(self, s3_key):
        """Monitorea el progreso del pipeline"""
        print("\n🔍 Monitoreando pipeline...")
        print("=" * 50)
        
        # Extraer nombre base del archivo
        base_name = s3_key.split('/')[-1].replace('.csv', '')
        
        expected_files = {
            'bronze': s3_key,
            'silver': f"silver/{base_name}.csv",
            'gold': f"gold/{base_name}_summary.csv",
            'anomalies': f"anomalies/{base_name}.csv"
        }
        
        for layer, expected_key in expected_files.items():
            try:
                # Verificar si el archivo existe en S3
                self.s3_client.head_object(Bucket=self.bucket_name, Key=expected_key)
                print(f"✅ {layer.upper()}: {expected_key} ✓")
                
                # Para gold, mostrar estadísticas
                if layer == 'gold':
                    response = self.s3_client.get_object(Bucket=self.bucket_name, Key=expected_key)
                    content = response['Body'].read().decode('utf-8')
                    lines = content.strip().split('\n')
                    print(f"   📈 {len(lines)-1} sensores procesados")
                    
            except Exception as e:
                if "404" in str(e):
                    print(f"⏳ {layer.upper()}: Esperando procesamiento...")
                else:
                    print(f"❌ {layer.upper()}: Error verificando - {str(e)}")
    
    def run_ingestion_pipeline(self, num_batches=3, records_per_batch=500):
        """Ejecuta el pipeline completo de ingesta"""
        print("=" * 60)
        print("🚀 INICIO DE INGESTA PROFESIONAL DE DATOS IoT")
        print("=" * 60)
        
        for batch in range(1, num_batches + 1):
            print(f"\n📦 LOTE {batch}/{num_batches}")
            print("-" * 40)
            
            # 1. Generar datos
            print("1. Generando datos IoT realistas...")
            df = self.generate_iot_data(
                num_records=records_per_batch,
                num_devices=random.randint(3, 8)
            )
            
            print(f"   ✅ {len(df)} registros generados")
            print(f"   📋 Dispositivos: {', '.join(df['device_id'].unique()[:3])}...")
            
            # 2. Guardar localmente
            print("\n2. Guardando respaldo local...")
            raw_file, processed_file = self.save_locally(df, batch)
            
            # 3. Subir a S3 (bronze)
            print("\n3. Subiendo a S3 (bronze layer)...")
            s3_key = self.upload_to_s3(df, batch)
            
            if s3_key:
                # 4. Esperar procesamiento
                print(f"\n4. Esperando procesamiento automático (15 segundos)...")
                import time
                time.sleep(15)
                
                # 5. Monitorear resultados
                self.monitor_pipeline(s3_key)
            
            print(f"\n{'='*60}")
        
        print("\n🎉 INGESTA COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        
        # Resumen final
        self.show_final_summary()
    
    def show_final_summary(self):
        """Muestra resumen final de todos los datos"""
        print("\n📊 RESUMEN FINAL DEL DATA LAKE")
        print("=" * 50)
        
        layers = ['bronze', 'silver', 'gold', 'anomalies']
        
        for layer in layers:
            try:
                # Listar archivos en cada capa
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=f"{layer}/"
                )
                
                if 'Contents' in response:
                    files = response['Contents']
                    total_size = sum(f['Size'] for f in files) / 1024  # KB
                    
                    print(f"{layer.upper():10} → {len(files):3} archivos | {total_size:7.1f} KB")
                    
                    # Mostrar últimos 2 archivos
                    recent_files = sorted(files, key=lambda x: x['LastModified'], reverse=True)[:2]
                    for f in recent_files:
                        filename = f['Key'].split('/')[-1]
                        size_kb = f['Size'] / 1024
                        print(f"           • {filename[:30]:30} ({size_kb:.1f} KB)")
                else:
                    print(f"{layer.upper():10} → 0 archivos")
                    
            except Exception as e:
                print(f"{layer.upper():10} → Error: {str(e)}")
        
        print("\n💡 Comandos para verificar manualmente:")
        print(f"  aws s3 ls s3://{self.bucket_name}/bronze/ --recursive")
        print(f"  aws s3 ls s3://{self.bucket_name}/gold/ --recursive")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IoT Data Ingestion Pipeline')
    parser.add_argument('--batches', type=int, default=3, help='Número de lotes a generar')
    parser.add_argument('--records', type=int, default=300, help='Registros por lote')
    parser.add_argument('--bucket', type=str, default='vantageflow-dev-data-lake-21bcb50a',
                       help='Nombre del bucket S3')
    
    args = parser.parse_args()
    
    print("🔧 Configuración:")
    print(f"   • Bucket S3: {args.bucket}")
    print(f"   • Lotes: {args.batches}")
    print(f"   • Registros/lote: {args.records}")
    print(f"   • Total estimado: {args.batches * args.records} registros")
    
    # Crear ingestor
    ingestor = IoTDataIngestor(bucket_name=args.bucket)
    
    # Ejecutar pipeline
    ingestor.run_ingestion_pipeline(
        num_batches=args.batches,
        records_per_batch=args.records
    )

if __name__ == "__main__":
    main()