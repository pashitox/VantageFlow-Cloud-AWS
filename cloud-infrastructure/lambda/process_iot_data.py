import json
import boto3
import csv
import io

s3 = boto3.client("s3")

def lambda_handler(event, context):
    print("=== VANTAGEFLOW LAMBDA ===")
    print(json.dumps(event, indent=2))

    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    if not key.endswith(".csv"):
        print("No es CSV, se ignora")
        return {"statusCode": 200}

    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read().decode("utf-8")

    reader = csv.reader(io.StringIO(body))
    rows = list(reader)

    print(f"Filas leídas: {len(rows)}")

    new_key = key.replace("bronze/", "silver/")

    s3.put_object(
        Bucket=bucket,
        Key=new_key,
        Body=body
    )

    print(f"✅ Guardado: s3://{bucket}/{new_key}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "archivo": key,
            "salida": new_key,
            "filas": len(rows)
        })
    }
