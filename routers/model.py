import os
import shutil
import tempfile
from fastapi import HTTPException, status, APIRouter, Depends, Query
from bson import ObjectId
from gridfs import GridFS
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
from database import fileDB, fs, get_fs,chatDB  # Assuming you have a database and fs setup
from pydantic import BaseModel
from typing import Optional
from repository import llm_qna
# Initialize the Whisper model
model = WhisperModel("small.en")  # Load the Whisper model

router = APIRouter(
    tags=["model"],
    prefix="/model",
)

import os
import shutil
import tempfile
from fastapi import HTTPException, status, APIRouter, Depends, Query
from bson import ObjectId
from gridfs import GridFS
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
from database import fileDB, fs, get_fs, chatDB  # Assuming you have chatDB setup for insertion
from pydantic import BaseModel
from typing import Optional

# Initialize the Whisper model
model = WhisperModel("small.en")  # Load the Whisper model

router = APIRouter(
    tags=["model"],
    prefix="/model",
)

@router.post('/transcribe/{file_id}')
async def transcribe(file_id: str, qno: Optional[int] = Query(None), fs: GridFS = Depends(get_fs)):
    temp_file_name = None
    try:
        # Convert file_id to ObjectId and fetch the file from GridFS
        file_object_id = ObjectId(file_id)
        audio_file = fileDB.find_one({"_id": file_object_id})
        if not audio_file:
            raise HTTPException(status_code=404, detail="File not found in database.")

        # Retrieve the file from GridFS
        file = fs.get(audio_file["file_id"])

        # Create a temporary file to store the audio content
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_name = temp_file.name  # Save the name of the temporary file

            # Copy the content from GridFS to the temp file
            with open(temp_file_name, 'wb') as f:
                shutil.copyfileobj(file, f)

        # Process the audio file with Whisper model
        segments, info = model.transcribe(
            temp_file_name,
            multilingual=False,
            task="translate",
        )

        # Create transcription result
        docs = " ".join([segment.text for segment in segments])
        output = llm_qna.create_qa_chain([docs],qno)
        result = {
            "response": docs,
            "language": info.language,
            "probability": info.language_probability,
            "qno": qno,
            "output": output,
        }

        # Prepare the data for insertion into chatDB, merging the previous data from fileDB
        chat_data = {
            "original_file_data": audio_file,  # Including all the data from the fileDB document
            "transcription": docs,
            "language": info.language,
            "language_probability": info.language_probability,
            "qno": qno,
            "file_object_id": file_object_id  # Store the file ObjectId in chatDB
        }

        # Insert the combined data into chatDB
        chat_insert_result = chatDB.insert_one(chat_data)

        # Check if the insertion was successful
        if not chat_insert_result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to insert transcription data into chatDB.")

        # Return the transcription result as a JSON response
        return JSONResponse(content=result, status_code=status.HTTP_200_OK)

    except Exception as e:
        # Log and handle any errors that occur during transcription
        print(f"Error during transcription: {str(e)}")  # Debugging log
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in transcription: {str(e)}"
        )

    finally:
        # Ensure cleanup happens in the 'finally' block to guarantee it's executed
        if temp_file_name:
            try:
                # Remove the temporary file if it exists
                if os.path.exists(temp_file_name):
                    os.remove(temp_file_name)
            except Exception as cleanup_error:
                # Handle any error that might occur during file cleanup
                print(f"Error cleaning up temp file: {cleanup_error}")  # Debugging log

