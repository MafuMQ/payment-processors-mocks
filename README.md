# Payment Processors Mocks

Mock APIs for various payment processors with persistent state tracking.

## Payshap API Mock

A stateful Flask application that mocks the Payshap payment API with realistic state transitions.

### Features

✨ **Stateful Processing**: Transactions progress through states over time
- `initiated` → `pending` → `completed`/`failed`
- Random processing delays (1-6 seconds total)
- 80% success rate, 20% failure rate

💾 **Persistent Storage**: SQLite database tracks all transactions

🔄 **Background Worker**: Automatically processes transactions through states

### API Endpoints

#### POST /api/payshap
Initiate a payment transaction.

**Request:**
```bash
curl -X POST http://localhost:8080/api/payshap \
  -H "Content-Type: application/json" \
  -d '{
    "shap_id_sender": "sender-123",
    "shap_id_receiver": "receiver-456",
    "amount": 100.50
  }'
```

**Response:**
```json
{
  "status": "initiated",
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "shap_id_sender": "sender-123",
  "shap_id_receiver": "receiver-456",
  "amount": 100.50
}
```

#### GET /api/payshap-status
Check transaction status (will show real-time state progression).

**Request:**
```bash
curl "http://localhost:8080/api/payshap-status?transaction_id=550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "status": "pending",
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "shap_id_sender": "sender-123",
  "shap_id_receiver": "receiver-456",
  "amount": 100.50,
  "created_at": "2026-04-17T10:30:00",
  "updated_at": "2026-04-17T10:30:02",
  "message": "Transaction is currently pending"
}
```

#### GET /api/payshap/all
Get all transactions (debugging endpoint).

#### GET /health
Health check endpoint.

---

## Deployment Options

### Option 1: GCP Compute Engine (Recommended for Persistence)

#### Quick Deploy
```bash
# 1. Edit deploy-gcp.sh and set your PROJECT_ID
# 2. Run deployment script
chmod +x deploy-gcp.sh
./deploy-gcp.sh

# 3. Copy files to instance
gcloud compute scp app.py requirements.txt payshap-mock-api:/opt/payshap-mock --zone=us-central1-a

# 4. SSH and start service
gcloud compute ssh payshap-mock-api --zone=us-central1-a
cd /opt/payshap-mock
sudo systemctl start payshap-mock
```

#### Manual Setup
```bash
# Create VM instance
gcloud compute instances create payshap-mock-api \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=debian-11 \
  --image-project=debian-cloud

# SSH into instance
gcloud compute ssh payshap-mock-api --zone=us-central1-a

# On the VM:
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv
mkdir -p /opt/payshap-mock
cd /opt/payshap-mock

# Upload your files, then:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Option 2: Docker

```bash
# Build and run with Docker
docker build -t payshap-mock .
docker run -p 8080:8080 -v $(pwd)/data:/app/data payshap-mock

# Or use Docker Compose
docker-compose up -d
```

### Option 3: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# API available at http://localhost:8080
```

---

## Testing

### Test Script
```bash
python test_api.py
```

### Manual Testing
```bash
# Create a transaction
TRANSACTION_ID=$(curl -X POST http://localhost:8080/api/payshap \
  -H "Content-Type: application/json" \
  -d '{"shap_id_sender":"test1","shap_id_receiver":"test2","amount":50}' \
  | jq -r '.transaction_id')

# Check status immediately (should be "initiated")
curl "http://localhost:8080/api/payshap-status?transaction_id=$TRANSACTION_ID" | jq

# Wait 2 seconds and check again (should be "pending")
sleep 2
curl "http://localhost:8080/api/payshap-status?transaction_id=$TRANSACTION_ID" | jq

# Wait 4 more seconds and check again (should be "completed" or "failed")
sleep 4
curl "http://localhost:8080/api/payshap-status?transaction_id=$TRANSACTION_ID" | jq
```

---

## Architecture

### State Transitions
```
initiated (1-3s) → pending (2-3s) → completed/failed
                                  → failed (20% chance)
```

### Components
- **Flask API**: Handles HTTP requests
- **SQLite Database**: Stores transaction state
- **Background Worker**: Thread that processes transactions through states
- **CORS Support**: Allows cross-origin requests

### Database Schema
```sql
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    shap_id_sender TEXT NOT NULL,
    shap_id_receiver TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    will_succeed INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

---

## Production Considerations

### GCP Compute Engine
- Use e2-micro for free tier (744 hours/month)
- Database persists on VM disk
- Consider backing up `/opt/payshap-mock/payshap.db`
- Use systemd for auto-restart on failure

### Scaling
For production loads, consider:
- Use Cloud SQL instead of SQLite
- Deploy multiple instances behind a load balancer
- Use Redis for transaction state
- Implement proper logging and monitoring

### Security
- Add authentication/API keys
- Use HTTPS (setup with Nginx reverse proxy)
- Firewall rules to restrict access
- Environment variables for configuration

---

## Monitoring

### Check Service Status (GCP VM)
```bash
sudo systemctl status payshap-mock
```

### View Logs
```bash
sudo journalctl -u payshap-mock -f
```

### Database Inspection
```bash
sqlite3 payshap.db "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10;"
```
