#!/bin/bash
# Deploy to GCP Compute Engine

# Configuration
PROJECT_ID="your-gcp-project-id"
INSTANCE_NAME="payshap-mock-api"
ZONE="us-central1-a"
MACHINE_TYPE="e2-micro"  # Free tier eligible
IMAGE_FAMILY="debian-11"
IMAGE_PROJECT="debian-cloud"

echo "🚀 Deploying Payshap Mock API to GCP Compute Engine"
echo "=================================================="

# Create instance
echo "Creating VM instance..."
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=10GB \
    --boot-disk-type=pd-standard \
    --tags=http-server,https-server \
    --metadata-from-file=startup-script=startup-script.sh

# Create firewall rule for port 8080
echo "Creating firewall rule..."
gcloud compute firewall-rules create allow-payshap-api \
    --project=$PROJECT_ID \
    --allow=tcp:8080 \
    --target-tags=http-server \
    --description="Allow access to Payshap Mock API on port 8080"

# Wait for instance to be ready
echo "Waiting for instance to start..."
sleep 30

# Get external IP
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME \
    --zone=$ZONE \
    --project=$PROJECT_ID \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "✅ Deployment initiated!"
echo "=================================================="
echo "Instance Name: $INSTANCE_NAME"
echo "External IP: $EXTERNAL_IP"
echo ""
echo "Copy files to instance:"
echo "gcloud compute scp app.py requirements.txt $INSTANCE_NAME:/opt/payshap-mock --zone=$ZONE"
echo ""
echo "SSH into instance:"
echo "gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
echo "API will be available at:"
echo "http://$EXTERNAL_IP:8080/api/payshap"
echo "http://$EXTERNAL_IP:8080/api/payshap-status?transaction_id=xxx"
echo ""
echo "Check logs:"
echo "gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='sudo journalctl -u payshap-mock -f'"
