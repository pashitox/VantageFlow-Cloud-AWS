import json
import boto3
import csv
import io

s3 = boto3.client("s3")

# Umbral para considerar un dato como anomalía
ANOMALY_THRESHOLD = 0.5

def lambda_handler(event, context):
    print("=== VANTAGEFLOW LAMBDA ===")
    print(json.dumps(event, indent=2))

    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    if not key.endswith(".csv"):
        print("No es CSV, se ignora")
        return {"statusCode": 200}

    # Leer CSV desde S3
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(body))
    rows = list(reader)
    print(f"Filas leídas: {len(rows)}")

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

    # Guardar datos normales en silver/
    silver_key = key.replace("bronze/", "silver/")
    write_csv_to_s3(bucket, silver_key, normal_rows, reader.fieldnames)
    print(f"✅ Silver guardado: s3://{bucket}/{silver_key}")

    # Guardar anomalías en anomalies/
    anomalies_key = key.replace("bronze/", "anomalies/")
    write_csv_to_s3(bucket, anomalies_key, anomalies_rows, reader.fieldnames)
    print(f"⚠️ Anomalías guardadas: s3://{bucket}/{anomalies_key}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "archivo": key,
            "filas_totales": len(rows),
            "filas_silver": len(normal_rows),
            "filas_anomalies": len(anomalies_rows),
            "silver_key": silver_key,
            "anomalies_key": anomalies_key
        })
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
