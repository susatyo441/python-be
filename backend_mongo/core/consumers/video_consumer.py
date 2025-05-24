import os, json, base64, cv2, numpy as np
from ultralytics import YOLO
from channels.generic.websocket import AsyncWebsocketConsumer
from bson import ObjectId
from core.models.product import Product
from core.utils.response import convert_mongo_types
import mediapipe as mp
# from datetime import datetime

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
model_path  = os.path.join(BASE_DIR, "modeln2.pt")
yaml_path   = os.path.join(BASE_DIR, "test.yaml")
MISS_TOLERANCE = 5

mp_hands = mp.solutions.hands
hands    = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

class VideoStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prev_tracks        = {}
        self.last_seen          = {}
        self.detected_track_ids = set()
        self.product_counts     = {}
        self.frame_count        = 0
        self.model              = None
        # self.frame_folder       = None
        self.product_cache = {}  


    async def connect(self):
        await self.accept()
        self.model = YOLO(model_path)

        # Buat folder baru utk sesi ini
        # ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # self.frame_folder = os.path.join(BASE_DIR, f"session_{ts}")
        # os.makedirs(self.frame_folder, exist_ok=True)
        # print(f"[VideoStreamConsumer] Saving frames to {self.frame_folder}")

        await self.send(json.dumps({"message": "connected"}))

    async def disconnect(self, close_code):
        # nothing to clean up here for images
        pass

    async def process_frame(self, frame):
        self.frame_count += 1

        # 1. (opsional) Hand skip
        # rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # if hands.process(rgb).multi_hand_landmarks:
        #     self.prev_tracks = {}
        #     return {"status": "hand_detected"}

        # 2. Deteksi & tracking
        results = self.model.track(
            frame, persist=True,
            conf=0.85, iou=0.15,
            tracker=yaml_path
        )

        current = {}
        for res in results:
            for box in res.boxes:
                if box.id is None: continue
                tid = int(box.id[0])
                lbl = self.model.names[int(box.cls[0])]
                current[tid] = lbl

                # gambar bounding box + label
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, f"{lbl}-{tid}",
                            (x1, y1-6),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0,255,0), 1)

        # 3. Konfirmasi dua-frame
        if self.frame_count > 2:
            confirmed = {
                tid: lbl for tid,lbl in current.items()
                if tid in self.prev_tracks
            }
        else:
            confirmed = current

        # 4. Hitung dengan miss-tolerance
        for tid, lbl in confirmed.items():
            last = self.last_seen.get(tid)
            if last is None or (self.frame_count - last) > MISS_TOLERANCE:
                self.product_counts[lbl] = self.product_counts.get(lbl, 0) + 1
            self.last_seen[tid] = self.frame_count

        self.prev_tracks = current.copy()

        # 5. Overlay counter
        y0 = 20
        for prod, cnt in self.product_counts.items():
            cv2.putText(frame, f"{prod}: {cnt}",
                        (10, y0),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255,0,0), 2)
            y0 += 25

        # 6. Simpan frame ke folder sesi
        # frame_path = os.path.join(
        #     self.frame_folder,
        #     f"frame_{self.frame_count:05d}.jpg"
        # )
        # cv2.imwrite(frame_path, frame)

        # 7. Siapkan data utk response, dengan cache
        products = []
        for lbl, cnt in self.product_counts.items():
            if lbl not in self.product_cache:
                try:
                    prod = Product.objects.get(id=ObjectId(lbl))
                    data = prod.to_mongo().to_dict()
                    # simpan tanpa quantity
                    self.product_cache[lbl] = data
                except Product.DoesNotExist:
                    # jika gagal ambil dari DB, skip dan jangan cache
                    continue

            # salin template data dan tambahkan quantity
            entry = self.product_cache[lbl].copy()
            entry["quantity"] = cnt
            products.append(entry)

        return {"status": "success", "products": convert_mongo_types(products)}


    async def receive(self, text_data):
        data      = json.loads(text_data)
        frame_b64 = data.get("frame")
        if not frame_b64:
            return

        buf   = base64.b64decode(frame_b64)
        arr   = np.frombuffer(buf, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        result = await self.process_frame(frame)
        if result["status"] == "hand_detected":
            await self.send(json.dumps({
                "message": "Hand Detected - Frame Skipped",
                "status": 200
            }))
        else:
            await self.send(json.dumps({
                "message": "Product Detected",
                "status": 200,
                "data": result["products"]
            }))