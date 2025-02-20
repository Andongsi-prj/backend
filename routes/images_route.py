from flask import Blueprint, jsonify
from kafka import KafkaConsumer, KafkaProducer
import base64
import time
import json
from queue import Queue
import threading
from db import get_db_connection

images_route = Blueprint('images_route', __name__)

# Kafka 설정
KAFKA_BROKER = '5gears.iptime.org:9092'
TOPIC_NAME = 'process_topic'
ACK_TOPIC = 'ack_topic'

# Kafka Producer 설정
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Kafka Consumer 설정
consumer = KafkaConsumer(
<<<<<<< HEAD
    'aa_topic',  # Topic 이름 (프로듀서와 동일한 토픽 사용)
    bootstrap_servers=['192.168.0.163:9092'],  # Kafka 브로커 주소
    auto_offset_reset='latest',  # 최신 메시지부터 읽기
    enable_auto_commit=True,  # 자동 오프셋 커밋
    group_id='image_consumer_group',  # Consumer 그룹 ID
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # JSON 역직렬화
=======
    TOPIC_NAME,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    enable_auto_commit=False,
    group_id='image_consumer_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# ACK Consumer (재사용 가능하도록 전역으로 생성)
ack_consumer = KafkaConsumer(
    ACK_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    group_id='ack_consumer_group',
    auto_offset_reset='earliest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
>>>>>>> 58445be5501f17d08260a11cea43f0e11894eff0
)

# 메시지를 저장할 큐 생성 (FIFO)
message_queue = Queue()

# 스레드 실행 여부 플래그
threads_started = False

# 이미지 인코딩 함수
def encode_image(image_data):
    return base64.b64encode(image_data).decode('utf-8')

# MySQL에서 이미지를 가져와 Kafka로 전송
def fetch_and_send_images():
    try:
        con = get_db_connection()
        last_acknowledged = None

        while True:
            with con.cursor() as cur:
                if last_acknowledged:
                    query = "SELECT img, plt_number FROM plt_img WHERE plt_number > %s ORDER BY plt_number ASC LIMIT 1"
                    cur.execute(query, (last_acknowledged,))
                else:
                    query = "SELECT img, plt_number FROM plt_img ORDER BY plt_number ASC LIMIT 1"
                    cur.execute(query)

                data = cur.fetchone()
                if data:
                    img, plt_number = data
                    encoded_image = encode_image(img)

                    message = {'plt_number': plt_number, 'encoded_image': encoded_image}
                    producer.send(TOPIC_NAME, value=message)
                    producer.flush()
                    print(f"Sent image with plt_number: {plt_number}")

                    ack_timeout = 10
                    start_time = time.time()

                    for ack_message in ack_consumer:
                        ack_data = ack_message.value
                        if ack_data.get('plt_number') == plt_number and ack_data.get('status') == 'processed':
                            print(f"Received ACK for plt_number: {plt_number}")
                            last_acknowledged = plt_number
                            break

                        if time.time() - start_time > ack_timeout:
                            print(f"ACK timeout for plt_number: {plt_number}")
                            break
                else:
                    print("No new images to process.")
                time.sleep(7)

    except Exception as e:
        print(f"Error in producer thread: {e}")

def consume_kafka_messages():
    """Kafka 메시지를 소비하고 처리 완료 후 ACK 신호를 전송"""
    try:
        for message in consumer:
            data = message.value
            plt_number = data.get('plt_number')
            encoded_image = data.get('encoded_image')

            if encoded_image:
                message_queue.put({
                    "plt_number": plt_number,
                    "encoded_image": f"data:image/png;base64,{encoded_image}"
                })
                print(f"Processed message for plt_number: {plt_number}")

                ack_message = {'status': 'processed', 'plt_number': plt_number}
                producer.send(ACK_TOPIC, value=ack_message)
                producer.flush()
                print(f"Sent ACK for plt_number: {plt_number}")
            consumer.commit()
    except Exception as e:
        print(f"Error in consumer thread: {e}")

@images_route.route('/images', methods=['POST'])
def get_images():
    global threads_started

    if not threads_started:
        threading.Thread(target=fetch_and_send_images, daemon=True).start()
        threading.Thread(target=consume_kafka_messages, daemon=True).start()
        threads_started = True

    timeout = 10
    start_time = time.time()

    while message_queue.empty():
        elapsed_time = time.time() - start_time
        print(f"Queue size before timeout check: {message_queue.qsize()}, Elapsed time: {elapsed_time:.2f}s")
        
        if elapsed_time > timeout:
            return jsonify({'message': 'No images available yet.'}), 404
        
        time.sleep(1)

<<<<<<< HEAD
# @images_route.route('/queue-status', methods=['GET'])
# def get_queue_status():
#     """큐의 현재 상태를 반환합니다"""
#     try:
#         queue_size = message_queue.qsize()
#         return jsonify({
#             'status': 'success',
#             'queue_size': queue_size,
#             'has_messages': not message_queue.empty()
#         }), 200
#     except Exception as e:
#         return jsonify({
#             'status': 'error',
#             'message': str(e)
#         }), 500





=======
    print(f"Queue size : {message_queue.qsize()}")
    next_message = message_queue.get()
    return jsonify({
        'status': 'success',
        'plt_number': next_message['plt_number'],
        'image': next_message['encoded_image']
    }), 200
>>>>>>> 58445be5501f17d08260a11cea43f0e11894eff0
