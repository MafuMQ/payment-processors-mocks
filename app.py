import time
import uuid
import random
import sqlite3
import threading
import requests
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = 'payshap.db'
MAX_WEBHOOK_ATTEMPTS = 3
WEBHOOK_TIMEOUT = 10  # seconds

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database"""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            shap_id_sender TEXT NOT NULL,
            shap_id_receiver TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            will_succeed INTEGER NOT NULL,
            webhook_url TEXT,
            webhook_status TEXT DEFAULT 'pending',
            webhook_attempts INTEGER DEFAULT 0,
            webhook_last_attempt_at TEXT,
            webhook_response_code INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def send_webhook(transaction_data):
    """Send webhook notification for completed transaction"""
    webhook_url = transaction_data.get('webhook_url')
    if not webhook_url:
        print(f"No webhook URL configured for transaction {transaction_data['transaction_id']}")
        return
    payload = {
        "event": f"transaction.{transaction_data['status']}",
        "transaction_id": transaction_data['transaction_id'],
        "status": transaction_data['status'],
        "shap_id_sender": transaction_data['shap_id_sender'],
        "shap_id_receiver": transaction_data['shap_id_receiver'],
        "amount": transaction_data['amount'],
        "created_at": transaction_data['created_at'],
        "completed_at": transaction_data['updated_at']
    }
    attempts = transaction_data.get('webhook_attempts', 0)
    for attempt in range(attempts, MAX_WEBHOOK_ATTEMPTS):
        try:
            print(f"Sending webhook for transaction {transaction_data['transaction_id']} (attempt {attempt + 1}/{MAX_WEBHOOK_ATTEMPTS})")
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=WEBHOOK_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            # Update webhook status in database
            conn = get_db()
            cursor = conn.cursor()
            if response.status_code in [200, 201, 202, 204]:
                # Success
                cursor.execute('''
                    UPDATE transactions
                    SET webhook_status = 'sent',
                        webhook_attempts = ?,
                        webhook_last_attempt_at = ?,
                        webhook_response_code = ?
                    WHERE transaction_id = ?
                ''', (attempt + 1, datetime.now().isoformat(), response.status_code, transaction_data['transaction_id']))
                conn.commit()
                conn.close()
                print(f"Webhook sent successfully for transaction {transaction_data['transaction_id']}")
                return
            else:
                # Non-success status code
                print(f"Webhook returned status {response.status_code} for transaction {transaction_data['transaction_id']}")
                cursor.execute('''
                    UPDATE transactions
                    SET webhook_attempts = ?,
                        webhook_last_attempt_at = ?,
                        webhook_response_code = ?
                    WHERE transaction_id = ?
                ''', (attempt + 1, datetime.now().isoformat(), response.status_code, transaction_data['transaction_id']))
                conn.commit()
                conn.close()
        except requests.exceptions.RequestException as e:
            print(f"Webhook delivery failed (attempt {attempt + 1}): {e}")
            # Update attempt count
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions
                SET webhook_attempts = ?,
                    webhook_last_attempt_at = ?
                WHERE transaction_id = ?
            ''', (attempt + 1, datetime.now().isoformat(), transaction_data['transaction_id']))
            conn.commit()
            conn.close()
        # Exponential backoff: wait 1s, 2s, 4s before retrying
        if attempt < MAX_WEBHOOK_ATTEMPTS - 1:
            wait_time = 2 ** attempt
            print(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    # All attempts failed
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transactions
        SET webhook_status = 'failed'
        WHERE transaction_id = ?
    ''', (transaction_data['transaction_id'],))
    conn.commit()
    conn.close()
    print(f"All webhook delivery attempts failed for transaction {transaction_data['transaction_id']}")

def process_transactions():
    """Background worker to process transactions through states"""
    while True:
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get all non-final transactions
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE status IN ('initiated', 'pending')
                ORDER BY created_at
            ''')
            
            transactions = cursor.fetchall()
            
            for txn in transactions:
                txn_id = txn['transaction_id']
                current_status = txn['status']
                will_succeed = txn['will_succeed']
                created_at = datetime.fromisoformat(txn['created_at'])
                age = (datetime.now() - created_at).total_seconds()
                
                new_status = current_status
                
                # State transitions based on age
                if current_status == 'initiated' and age > random.uniform(1, 3):
                    new_status = 'pending'
                elif current_status == 'pending' and age > random.uniform(3, 6):
                    new_status = 'completed' if will_succeed else 'failed'
                
                # Update if status changed
                if new_status != current_status:
                    cursor.execute('''
                        UPDATE transactions 
                        SET status = ?, updated_at = ?
                        WHERE transaction_id = ?
                    ''', (new_status, datetime.now().isoformat(), txn_id))
                    conn.commit()
                    print(f"Transaction {txn_id}: {current_status} -> {new_status}")
                    
                    # Send webhook if transaction reached final state
                    if new_status in ['completed', 'failed']:
                        # Fetch full transaction data and send webhook in separate thread
                        cursor.execute('SELECT * FROM transactions WHERE transaction_id = ?', (txn_id,))
                        txn_data = dict(cursor.fetchone())
                        webhook_thread = threading.Thread(
                            target=send_webhook,
                            args=(txn_data,),
                            daemon=True
                        )
                        webhook_thread.start()
            
            # Also retry failed webhooks that haven't reached max attempts
            cursor.execute('''
                SELECT * FROM transactions
                WHERE status IN ('completed', 'failed')
                AND webhook_status = 'pending'
                AND webhook_attempts < ?
                AND (webhook_last_attempt_at IS NULL 
                     OR datetime(webhook_last_attempt_at) < datetime('now', '-10 seconds'))
            ''', (MAX_WEBHOOK_ATTEMPTS,))
            
            retry_transactions = cursor.fetchall()
            for txn in retry_transactions:
                txn_data = dict(txn)
                webhook_thread = threading.Thread(
                    target=send_webhook,
                    args=(txn_data,),
                    daemon=True
                )
                webhook_thread.start()
            
            conn.close()
            time.sleep(1)  # Check every second
            
        except Exception as e:
            print(f"Error in background worker: {e}")
            time.sleep(1)

@app.route('/api/payshap', methods=['POST'])
def process_payment():
    """Initiate a payment transaction"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['shap_id_sender', 'shap_id_receiver', 'amount']
    if not all(field in data for field in required_fields):
        return jsonify({
            'error': 'Missing required fields: shap_id_sender, shap_id_receiver, amount'
        }), 400
    
    # Extract fields
    shap_id_sender = data['shap_id_sender']
    shap_id_receiver = data['shap_id_receiver']
    amount = data['amount']
    webhook_url = data.get('webhook_url')
    if not webhook_url:
        return jsonify({
            'error': 'Missing required field: webhook_url'
        }), 400
    # Generate transaction ID
    transaction_id = str(uuid.uuid4())
    # Determine if this transaction will succeed (80% success rate)
    will_succeed = 1 if random.random() < 0.8 else 0
    # Store in database
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO transactions 
        (transaction_id, shap_id_sender, shap_id_receiver, amount, status, will_succeed, webhook_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (transaction_id, shap_id_sender, shap_id_receiver, amount, 'initiated', will_succeed, webhook_url, now, now))
    conn.commit()
    conn.close()
    response_data = {
        "status": "initiated",
        "transaction_id": transaction_id,
        "shap_id_sender": shap_id_sender,
        "shap_id_receiver": shap_id_receiver,
        "amount": amount,
        "webhook_url": webhook_url
    }
    return jsonify(response_data), 201

@app.route('/api/payshap-status', methods=['GET'])
def get_status():
    """Check transaction status by ID"""
    transaction_id = request.args.get('transaction_id')
    
    if not transaction_id:
        return jsonify({
            'error': 'Missing required parameter: transaction_id'
        }), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM transactions WHERE transaction_id = ?', (transaction_id,))
    txn = cursor.fetchone()
    conn.close()
    
    if not txn:
        return jsonify({
            'error': 'Transaction not found'
        }), 404
    
    return jsonify({
        "status": txn['status'],
        "transaction_id": txn['transaction_id'],
        "shap_id_sender": txn['shap_id_sender'],
        "shap_id_receiver": txn['shap_id_receiver'],
        "amount": txn['amount'],
        "created_at": txn['created_at'],
        "updated_at": txn['updated_at'],
        "webhook_status": txn['webhook_status'],
        "webhook_attempts": txn['webhook_attempts'],
        "message": f"Transaction is currently {txn['status']}"
    })

@app.route('/api/payshap/all', methods=['GET'])
def get_all_transactions():
    """Get all transactions (for debugging)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM transactions ORDER BY created_at DESC LIMIT 100')
    transactions = cursor.fetchall()
    conn.close()
    
    return jsonify({
        "transactions": [dict(txn) for txn in transactions]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start background worker thread
    worker = threading.Thread(target=process_transactions, daemon=True)
    worker.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8080, debug=False)
