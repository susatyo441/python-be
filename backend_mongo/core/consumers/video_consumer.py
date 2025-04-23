import base64
import cv2
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
import json
from bson import ObjectId
import os
from ultralytics import YOLO
from core.models.product import Product
from core.utils.response import convert_mongo_types
from deep_sort_realtime.deepsort_tracker import DeepSort

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "best11x2.pt")
model = YOLO(model_path)
# Tambahkan ini di awal file atau dalam __init__ jika kamu buatnya kelas stateful
tracker = DeepSort(max_age=15, n_init=2)  # max_age = berapa banyak frame objek boleh 'hilang'

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(json.dumps({"message": "connected"}))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        frame_b64 = data.get("frame")
        if not frame_b64:
            return

        frame_data = base64.b64decode(frame_b64)
        np_arr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # YOLO Detection
        results = model(frame)
        detections = []
        print("Detected classes:", [model.names[int(c)] for r in results for c in r.boxes.cls])
        
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls)
                conf = float(box.conf)
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # assuming box format is xyxy
                detections.append(([x1, y1, x2 - x1, y2 - y1], conf, cls_id))

        tracks = tracker.update_tracks(detections, frame=frame)

        product_ids = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            class_id = track.get_det_class()  # Optional: if DeepSort supports this or store manually
            product_name = model.names[class_id]
            try:
                object_id = ObjectId(product_name.strip())
                product = Product.objects.get(id=object_id)
                product_ids.append(product.pk)
            except Exception as e:
                print(f"Track {track_id}: failed to fetch product: {e}")

        print("Product IDs:", product_ids)

        products = Product.objects(id__in=product_ids)
        result = [p.to_mongo().to_dict() for p in products]

        await self.send(text_data=json.dumps({
            "message": "Product Detected",
            "status": 200,
            "data": convert_mongo_types(result)
        }))
