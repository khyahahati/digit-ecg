from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from digit_ecg_tool.ecg_pipeline import ecg_image_to_features

app = FastAPI()

@app.post("/extract-ecg-features/")
async def extract_ecg_features(file: UploadFile = File(...)):
    try:
        img_bytes = await file.read()
        df = ecg_image_to_features(img_bytes)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))