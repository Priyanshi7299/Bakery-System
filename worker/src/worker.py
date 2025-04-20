import pika
import psycopg2
import json
import os
import time
import random

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('POSTGRES_DB', 'bakery'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
    )
    conn.autocommit = True
    return conn

def process_order(order_id):
    print(f"Processing order {order_id}")
    
    # Simulate order processing
    processing_time = random.randint(5, 15)
    print(f"Order {order_id} will take {processing_time} seconds to process")
    
    # Update order status to 'processing'
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = 'processing' WHERE id = %s", (order_id,))
    conn.close()
    
    # Simulate processing time
    time.sleep(processing_time)
    
    # Update order status to 'completed'
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = 'completed' WHERE id = %s", (order_id,))
    conn.close()
    
    print(f"Order {order_id} has been processed successfully")

def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        order_id = data.get('order_id')
        
        if order_id:
            process_order(order_id)
        else:
            print("Received message with no order_id")
            
    except Exception as e:
        print(f"Error processing message: {e}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # Wait for RabbitMQ to be ready
    max_retries = 30
    retries = 0
    connection = None
    
    while retries < max_retries:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            break
        except Exception as e:
            retries += 1
            print(f"Waiting for RabbitMQ ({retries}/{max_retries})...")
            time.sleep(2)
    
    if connection is None:
        print("Failed to connect to RabbitMQ, exiting...")
        exit(1)
    
    channel = connection.channel()
    channel.queue_declare(queue='order_processing')
    
    # Set prefetch count to 1 to ensure workers process one message at a time
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(
        queue='order_processing',
        on_message_callback=callback
    )
    
    print("Worker started. Waiting for orders...")
    channel.start_consuming()

if __name__ == '__main__':
    main()