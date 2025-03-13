import os
import shutil
from fastapi import APIRouter, UploadFile, HTTPException, File, Depends
from gridfs import GridFS
from bson import ObjectId
from fastapi.responses import StreamingResponse
from typing import List
from pymongo import MongoClient
from database import fileDB, fs, get_fs
import gridfs
from audio_extract import extract_audio

# Create a new router for file operations
router = APIRouter(
    tags=["File"],
    prefix="/file"
)

# Define a path for saving files in the static folder
STATIC_DIR = "static"  # The directory where you want to store the files

# Make sure the static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Upload file endpoint
@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), fs: GridFS = Depends(get_fs)):
    try:
        # File upload logic using GridFS
        file_id = fs.put(file.file, filename=file.filename, content_type=file.content_type)

        # Insert file metadata into fileDB
        file_metadata = {
            "file_id": file_id,
            "filename": file.filename,
        }

        # Save metadata in fileDB (assuming fileDB is a MongoDB collection)
        fileDB.insert_one(file_metadata)

        # Return the file_id and filename
        return {"file_id": str(file_id), "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Get file by file_id endpoint
@router.get("/{file_id}")
async def get_file(file_id: str, fs: GridFS = Depends(get_fs)):
    try:
        # Convert file_id to ObjectId
        file_object_id = ObjectId(file_id)

        # Try to find file metadata in fileDB using file_id
        audio_file = fileDB.find_one({"file_id": file_object_id})

        if not audio_file:
            raise HTTPException(status_code=404, detail="File metadata not found in database.")

        # Retrieve the file from GridFS
        file = fs.get(audio_file["file_id"])

        # Return the file as a StreamingResponse
        return StreamingResponse(file, media_type=file.content_type)

    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found in GridFS.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")


# Show all files metadata endpoint
@router.get("/all/")
async def show_all_files(fs: GridFS = Depends(get_fs)):
    try:
        # Get all files' metadata from the fileDB
        files = list(fileDB.find())  # Assuming fileDB contains metadata like filename, file_id, etc.

        # Convert ObjectId to string for JSON compatibility
        all_files = [{"file_id": str(file["_id"]), "filename": file["filename"]} for file in files]

        if not all_files:
            return {"message": "No files found."}

        return {"files": all_files}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")




# Delete file by file_id endpoint
@router.delete("/delete/{file_id}")
async def delete_file(file_id: str, fs: GridFS = Depends(get_fs)):
    try:
        # Convert file_id to ObjectId
        file_object_id = ObjectId(file_id)

        # Try to retrieve file metadata from fileDB
        file_info = fileDB.find_one({"_id": file_object_id})  # Use the _id field for lookup

        if not file_info:
            raise HTTPException(status_code=404, detail="File not found in metadata.")

        # Retrieve the file from GridFS using the file_id from fileDB
        try:
            file = fs.get(file_info['file_id'])  # If file doesn't exist, this will raise an exception
        except gridfs.errors.NoFile:
            raise HTTPException(status_code=404, detail="File not found in GridFS")

        # If file exists, delete it from GridFS
        fs.delete(file_info['file_id'])

        # Delete the file metadata from fileDB
        fileDB.delete_one({"_id": file_object_id})  # Use a dictionary filter for delete_one()

        return {"message": f"File with ID {file_id} has been deleted successfully."}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting file: {str(e)}")



@router.post("/upload-video/")
async def upload_video(file: UploadFile = File(...), fs: GridFS = Depends(get_fs)):
    try:
        # Validate file extension
        file_name = os.path.splitext(file.filename)[0].lower()

        # Define the paths for the uploaded video and output audio file in the static folder
        video_file_path = os.path.join(STATIC_DIR, f"{file_name}{os.path.splitext(file.filename)[1]}")
        audio_file_path = os.path.join(STATIC_DIR, f"{file_name}.mp3")

        # Save the uploaded video to the static folder
        with open(video_file_path, "wb") as video_file:
            video_file.write(await file.read())

        print(f"Video file saved at: {video_file_path}")
        print(f"Audio file path: {audio_file_path}")

        # Convert the video to audio using the extract_audio function
        extract_audio(input_path=video_file_path, output_path=audio_file_path)

        # Check if the audio file has been created
        if not os.path.exists(audio_file_path):
            raise HTTPException(status_code=500, detail="Audio extraction failed.")

        # Open the audio file and upload it to GridFS
        with open(audio_file_path, "rb") as audio_file:
            file_id = fs.put(audio_file, filename=f"{file_name}.mp3", content_type="audio/mpeg")

        # Insert audio file metadata into fileDB
        file_metadata = {
            "file_id": file_id,
            "filename": f"{file_name}.mp3",
        }

        # Save metadata in fileDB
        fileDB.insert_one(file_metadata)

        # Clean up static files
        os.remove(video_file_path)  # Delete the uploaded video file after processing
        os.remove(audio_file_path)  # Delete the audio file after uploading

        return {"file_id": str(file_id), "filename": f"{file_name}.mp3"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading and converting video: {str(e)}")


# Play (stream) file endpoint

