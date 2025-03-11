from fastapi import APIRouter, File, UploadFile, HTTPException, status
from schemas import user
from database import userDB, chatDB, fileDB
import shutil
import hashlib
from faster_whisper import WhisperModel
from audio_extract import extract_audio
from datetime import datetime

model_size = "base"
# Run on GPU with FP16
model = WhisperModel(model_size, device="cuda", compute_type="float16")

# Invalid model size 'base.bn', expected one of: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3, large, distil-large-v2, distil-medium.en, distil-small.en, distil-large-v3, large-v3-turbo, turbo

router = APIRouter(
    tags=["Model"],
    prefix="/model"
)

API_KEY = ""

@router.post('/{GOOGLE_API_KEY}')
def initializeLLM(GOOGLE_API_KEY: str):
    global API_KEY
    API_KEY = GOOGLE_API_KEY
    return {
        "API": GOOGLE_API_KEY,
    }, status.HTTP_200_OK  # Returning 200 OK

@router.get('/')
def getAPIKey():
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not set"
        )
    return {
        "API": API_KEY,
    }, status.HTTP_200_OK  # Returning 200 OK

@router.post('/transcribe/{audioUrl}')
def transcribe(audioUrl: str):
    try:
        segments, info = model.transcribe(
            audioUrl,
            multilingual=True,
            task="translate",
        )

        docs = " "

        for segment in segments:
            docs += segment.text

        result = {
            "response": docs,
            "response_info": {
                "predicted_language": info.language,
                "predicted_language_probability": info.language_probability
            }
        }
        chatDB.insert_one(result)
        return result, status.HTTP_200_OK  # Return 200 OK for successful transcription

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in transcription: {str(e)}"
        )

