from fastapi import APIRouter
from schemas import user
from database import userDB, chatDB
import torch
from faster_whisper import WhisperModel
from audio_extract import extract_audio

model_size = "tiny"
# Run on GPU with FP16
model = WhisperModel(model_size, device="cuda", compute_type="float16")

# Invalid model size 'base.bn', expected one of: tiny.en, tiny, base.en, base, small.en, small, medium.en, medium, large-v1, large-v2, large-v3, large, distil-large-v2, distil-medium.en, distil-small.en, distil-large-v3, large-v3-turbo, turbo

router = APIRouter(
    tags=["Model"],
    prefix="/model"
)
API_KEY =""
@router.post('/{GOOGLE_API_KEY}')
def initializeLLM(GOOGLE_API_KEY: str):
    API_KEY = GOOGLE_API_KEY
    return {
        "API": GOOGLE_API_KEY,
    }

@router.get('/')
def initializeLLM():
    return {
        "API": API_KEY,
    }

@router.post('/transcribe/{audioUrl}')
def transcribe(audioUrl: str):
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
            "predicted_language":info.language,
            "predicted_language_probability":info.language_probability
        }
    }
    chatDB.insert_one(result)
    return result

@router.post('/videotoaudio/{videoUrl}')
def convertVideoToAudio(videoUrl: str):
    output_path = r"Audios\bangla_audio.mp3"
    extract_audio(input_path=videoUrl, output_path=output_path)

    return {
        "Audio": output_path
    }
    