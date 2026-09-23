"""
Machine Status Prediction API
FastAPI service that serves a RandomForestClassifier trained to predict
machine status (Normal / Warning / Critical) from sensor readings.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import joblib
import pandas as pd
import os

# ---------------------------------------------------------------------------
# Load model
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(os.path.dirname(__file__), "machine_status_model.pkl")
model = joblib.load(MODEL_PATH)

# The exact column order the model was trained on
FEATURE_COLUMNS = list(model.feature_names_in_)

# Machine IDs the model knows about (MCH-01 is the one-hot baseline / dropped column)
MACHINE_IDS = [f"MCH-{i:02d}" for i in range(1, 21)]

MachineIdType = Literal[tuple(MACHINE_IDS)]  # type: ignore

app = FastAPI(
    title="Machine Status Prediction API",
    description="Predicts machine status (Normal / Warning / Critical) from sensor readings.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    temperature_c: float = Field(..., example=75.5, description="Machine temperature in Celsius")
    vibration_mm_s: float = Field(..., example=3.2, description="Vibration reading in mm/s")
    hour: int = Field(..., ge=0, le=23, example=14, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, example=2, description="Day of week (0=Monday ... 6=Sunday)")
    machine_id: MachineIdType = Field(..., example="MCH-05", description="Machine identifier (MCH-01 to MCH-20)")


class PredictionResponse(BaseModel):
    status: str
    probabilities: dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def build_feature_row(payload: PredictionRequest) -> pd.DataFrame:
    """Build a single-row DataFrame matching the model's expected columns
    (numeric features + one-hot encoded machine_id, MCH-01 as baseline)."""
    row = {col: 0 for col in FEATURE_COLUMNS}

    row["temperature_c"] = payload.temperature_c
    row["vibration_mm_s"] = payload.vibration_mm_s
    row["hour"] = payload.hour
    row["day_of_week"] = payload.day_of_week

    machine_col = f"machine_id_{payload.machine_id}"
    if machine_col in row:
        row[machine_col] = 1
    # if machine_id == MCH-01, all one-hot machine columns stay 0 (baseline)

    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Machine Status Prediction API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    try:
        X = build_feature_row(payload)
        prediction = model.predict(X)[0]
        proba = model.predict_proba(X)[0]
        probabilities = {cls: round(float(p), 4) for cls, p in zip(model.classes_, proba)}
        return PredictionResponse(status=str(prediction), probabilities=probabilities)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
