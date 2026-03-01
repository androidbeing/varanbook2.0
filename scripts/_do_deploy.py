import json, subprocess, sys, tempfile, os, time

FRONTEND_URL  = "https://d4eomqccsr1k1.cloudfront.net"
SERVICE_NAME  = "varanbook-api-production"
IMAGE_REF     = ":varanbook-api-production.api.2"
REGION        = "ap-south-1"

containers = {
    "api": {
        "image": IMAGE_REF,
        "ports": {"8000": "HTTP"},
        "environment": {
            "APP_ENV":               "production",
            "DEBUG":                 "false",
            "SECRET_KEY":            "kMRDN8oiWsR2nHgZMDxs0n4UQYsLBFkhf6H2tg7P",
            "DATABASE_URL":          "postgresql+asyncpg://postgres:268u*VgQKaHH@database-1.cfgssmaoudkt.ap-south-1.rds.amazonaws.com:5432/postgres",
            "DATABASE_POOL_SIZE":    "10",
            "DATABASE_MAX_OVERFLOW": "20",
            "AWS_REGION":            REGION,
            "S3_BUCKET_NAME":        "varanbook-media-production",
            # pydantic-settings List[str] requires a JSON-encoded array string
            "ALLOWED_ORIGINS":       json.dumps([FRONTEND_URL, "http://localhost:5173"]),
            "APP_FRONTEND_URL":      FRONTEND_URL,
            "SMTP_HOST":             "email-smtp.ap-south-1.amazonaws.com",
            "SMTP_PORT":             "587",
            "SMTP_USERNAME":         "",
            "SMTP_PASSWORD":         "",
            "SMTP_FROM":             "noreply@varanbook.in",
        }
    }
}

endpoint = {
    "containerName": "api",
    "containerPort": 8000,
    "healthCheck": {
        "healthyThreshold":   2,
        "unhealthyThreshold": 2,
        "timeoutSeconds":     10,
        "intervalSeconds":    30,
        "path":               "/health",
        "successCodes":       "200-299"
    }
}

tmp = tempfile.gettempdir()
cf = os.path.join(tmp, "ls-containers.json")
ef = os.path.join(tmp, "ls-endpoint.json")
with open(cf, "w") as f: json.dump(containers, f, indent=2)
with open(ef, "w") as f: json.dump(endpoint,   f, indent=2)

print("==> Creating Lightsail deployment (image:", IMAGE_REF, ")")
r = subprocess.run([
    "aws", "lightsail", "create-container-service-deployment",
    "--region", REGION,
    "--service-name", SERVICE_NAME,
    "--containers", f"file://{cf}",
    "--public-endpoint", f"file://{ef}",
    "--query", "containerService.currentDeployment.{version:version,state:state}",
    "--output", "table"
], capture_output=False, text=True)

if r.returncode != 0:
    print("ERROR: deployment creation failed")
    sys.exit(1)

print("\n==> Polling deployment state...")
state = ""
for i in range(24):
    time.sleep(15)
    s = subprocess.run([
        "aws", "lightsail", "get-container-service-deployments",
        "--region", REGION,
        "--service-name", SERVICE_NAME,
        "--query", "deployments[0].state",
        "--output", "text"
    ], capture_output=True, text=True)
    state = s.stdout.strip()
    print(f"  {(i+1)*15}s -> {state}")
    if state in ("ACTIVE", "FAILED"):
        break

print()
if state == "ACTIVE":
    print("SUCCESS: Backend live at https://varanbook-api-production.7t9yd18mf2e7j.ap-south-1.cs.amazonlightsail.com")
else:
    print(f"FAILED (state={state}) - check logs:")
    print("  aws lightsail get-container-log --region ap-south-1 --service-name varanbook-api-production --container-name api")
    sys.exit(1)
