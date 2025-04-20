from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
import pika
import json
import time
import redis

app = Flask(__name__)
CORS(app)

# Wait for PostgreSQL to be ready
def wait_for_postgres():
    max_retries = 30
    retries = 0
    while retries < max_retries:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'db'),
                database=os.environ.get('POSTGRES_DB', 'bakery'),
                user=os.environ.get('POSTGRES_USER', 'postgres'),
                password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
            )
            conn.close()
            return True
        except psycopg2.OperationalError:
            retries += 1
            print(f"Waiting for PostgreSQL ({retries}/{max_retries})...")
            time.sleep(2)
    return False

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('POSTGRES_DB', 'bakery'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
    )
    conn.autocommit = True
    return conn

# Try to connect to Redis if available
try:
    redis_client = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'redis'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
        db=0
    )
    use_redis = True
except:
    use_redis = False
    print("Redis not available, running without cache")

# RabbitMQ connection
def get_rabbitmq_connection():
    retries = 0
    max_retries = 30
    while retries < max_retries:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            return connection
        except Exception as e:
            retries += 1
            print(f"Waiting for RabbitMQ ({retries}/{max_retries})...")
            time.sleep(2)
    return None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/products', methods=['GET'])
def get_products():
    if use_redis:
        # Try to get products from cache first
        cached_products = redis_client.get('products')
        if cached_products:
            return jsonify(json.loads(cached_products))
    
    # If not in cache or no Redis, get from database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, price, in_stock FROM products')
    products = []
    for row in cur.fetchall():
        products.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': float(row[3]),
            'in_stock': row[4]
        })
    cur.close()
    conn.close()
    
    # Cache the result if Redis is available
    if use_redis:
        redis_client.setex('products', 300, json.dumps(products))  # Cache for 5 minutes
    
    return jsonify(products)

@app.route('/api/orders', methods=['POST'])
def place_order():
    data = request.get_json()
    
    if not data or 'customer_name' not in data or 'customer_email' not in data or 'items' not in data:
        return jsonify({"error": "Missing required data"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create order
    cur.execute(
        'INSERT INTO orders (customer_name, customer_email) VALUES (%s, %s) RETURNING id',
        (data['customer_name'], data['customer_email'])
    )
    order_id = cur.fetchone()[0]
    
    # Add order items
    for item in data['items']:
        cur.execute(
            'INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)',
            (order_id, item['product_id'], item['quantity'])
        )
    
    conn.close()
    
    # Send to RabbitMQ for processing
    try:
        connection = get_rabbitmq_connection()
        if connection:
            channel = connection.channel()
            channel.queue_declare(queue='order_processing')
            channel.basic_publish(
                exchange='',
                routing_key='order_processing',
                body=json.dumps({'order_id': order_id})
            )
            connection.close()
    except Exception as e:
        print(f"Failed to send to RabbitMQ: {e}")
    
    return jsonify({"message": "Order placed successfully", "order_id": order_id})

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT status FROM orders WHERE id = %s', (order_id,))
    result = cur.fetchone()
    
    if result is None:
        return jsonify({"error": "Order not found"}), 404
    
    conn.close()
    return jsonify({"order_id": order_id, "status": result[0]})

if __name__ == '__main__':
    # Wait for PostgreSQL to be available
    if not wait_for_postgres():
        print("Failed to connect to PostgreSQL, exiting...")
        exit(1)
        
    app.run(host='0.0.0.0', port=5000)