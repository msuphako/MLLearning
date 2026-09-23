# Machine Status Prediction API

FastAPI web service ที่ให้บริการโมเดล `RandomForestClassifier` เพื่อทำนายสถานะเครื่องจักร
(`Normal` / `Warning` / `Critical`) จากค่าที่อ่านได้จากเซ็นเซอร์

## โครงสร้างไฟล์

```
.
├── main.py                     # FastAPI application
├── machine_status_model.pkl    # โมเดลที่เทรนไว้แล้ว (joblib-pickled)
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render.com blueprint (deploy อัตโนมัติ)
└── README.md
```

## รันทดสอบบนเครื่องตัวเอง

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

เปิดดู interactive docs ที่ `http://localhost:8000/docs`

## Input ที่โมเดลต้องการ

| ฟิลด์ | ชนิด | คำอธิบาย |
|---|---|---|
| `temperature_c` | float | อุณหภูมิเครื่องจักร (°C) |
| `vibration_mm_s` | float | ค่าการสั่นสะเทือน (mm/s) |
| `hour` | int (0-23) | ชั่วโมงของวัน |
| `day_of_week` | int (0-6) | วันในสัปดาห์ (0=จันทร์ ... 6=อาทิตย์) |
| `machine_id` | string | รหัสเครื่องจักร `MCH-01` ถึง `MCH-20` |

### ตัวอย่างเรียก API

```bash
curl -X POST "https://<your-render-url>/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature_c": 82.5,
    "vibration_mm_s": 4.1,
    "hour": 14,
    "day_of_week": 2,
    "machine_id": "MCH-05"
  }'
```

### ตัวอย่าง response

```json
{
  "status": "Warning",
  "probabilities": {
    "Critical": 0.12,
    "Normal": 0.30,
    "Warning": 0.58
  }
}
```

## นำขึ้น GitHub

```bash
cd machine-status-api
git init
git add .
git commit -m "Initial commit: Machine Status Prediction API"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

> **หมายเหตุ:** ไฟล์ `.pkl` มีขนาดประมาณ 5 MB ซึ่งอยู่ในขีดจำกัดปกติของ GitHub (ไม่ต้องใช้ Git LFS)

## Deploy บน Render.com

**วิธีที่ 1 — ใช้ Blueprint (แนะนำ):**
1. Push โค้ดขึ้น GitHub ตามขั้นตอนด้านบน
2. เข้า Render Dashboard → **New** → **Blueprint**
3. เลือก repo นี้ Render จะอ่านค่าใน `render.yaml` และตั้งค่าให้อัตโนมัติ

**วิธีที่ 2 — สร้าง Web Service เอง:**
1. เข้า Render Dashboard → **New** → **Web Service**
2. เชื่อมต่อกับ GitHub repo นี้
3. ตั้งค่า:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3
4. กด **Create Web Service**

หลัง deploy เสร็จ จะได้ URL เช่น `https://machine-status-api.onrender.com` และสามารถทดสอบผ่าน `/docs` ได้ทันที

## Endpoints

| Method | Path | คำอธิบาย |
|---|---|---|
| GET | `/` | ตรวจสอบว่า service ทำงานอยู่ |
| GET | `/health` | Health check พร้อมสถานะโมเดล |
| POST | `/predict` | ทำนายสถานะเครื่องจักร |
| GET | `/docs` | Swagger UI (interactive API docs) |
