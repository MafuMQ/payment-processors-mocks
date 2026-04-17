import requests
import json
import time

# Test the Payshap mock API
BASE_URL = "http://34.67.233.58:8080"  # Change to your GCP VM IP when deployed

def test_payment():
    """Test the payment endpoint with state transitions"""
    print("🧪 Testing POST /api/payshap")
    print("-" * 50)
    
    payload = {
        "shap_id_sender": "sender-test-123",
        "shap_id_receiver": "receiver-test-456",
        "amount": 250.75
    }
    
    print(f"Sending payment request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/api/payshap", json=payload)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"\nInitial Response: {json.dumps(result, indent=2)}")
        
        # Test status endpoint with state transitions
        transaction_id = result.get('transaction_id')
        if transaction_id:
            print(f"\n🧪 Testing GET /api/payshap-status - Watching state transitions")
            print("-" * 50)
            
            for i in range(8):
                time.sleep(1)
                status_response = requests.get(
                    f"{BASE_URL}/api/payshap-status",
                    params={"transaction_id": transaction_id}
                )
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    print(f"[{i+1}s] Status: {status}")
                    
                    if status in ['completed', 'failed']:
                        print(f"\n✅ Final state reached: {status}")
                        print(f"Full response: {json.dumps(status_data, indent=2)}")
                        break
    else:
        print(f"Error: {response.text}")

def test_multiple_payments():
    """Test multiple payments to see different outcomes"""
    print("\n\n🧪 Testing multiple payments for different statuses")
    print("-" * 50)
    
    transactions = []
    
    # Create multiple transactions
    for i in range(5):
        print(f"\nPayment {i + 1}:")
        payload = {
            "shap_id_sender": f"sender-{i}",
            "shap_id_receiver": f"receiver-{i}",
            "amount": (i + 1) * 50
        }
        
        response = requests.post(f"{BASE_URL}/api/payshap", json=payload)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"  Initial Status: {result['status']}")
            print(f"  Transaction ID: {result['transaction_id']}")
            print(f"  Amount: {result['amount']}")
            transactions.append(result['transaction_id'])
    
    # Wait and check final status of all transactions
    print(f"\n⏳ Waiting 7 seconds for transactions to complete...")
    time.sleep(7)
    
    print("\n📊 Final Status of All Transactions:")
    print("-" * 50)
    for idx, txn_id in enumerate(transactions, 1):
        status_response = requests.get(
            f"{BASE_URL}/api/payshap-status",
            params={"transaction_id": txn_id}
        )
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get('status')
            amount = status_data.get('amount')
            print(f"Transaction {idx}: {status:10} | Amount: ${amount} | ID: {txn_id[:8]}...")

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("Payshap Mock API Test Suite")
        print("=" * 50)
        
        test_payment()
        test_multiple_payments()
        
        print("\n\n✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API")
        print("Make sure the server is running with 'python app.py'")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
