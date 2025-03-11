import shutil
import hashlib
import os
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from database import fileDB  # Your MongoDB database instance

router = APIRouter(
    tags=["File Upload"],
    prefix="/files"
)

# Ensure the 'static' directory exists
if not os.path.exists("static"):
    os.makedirs("static")


def calculate_file_hash(file: UploadFile) -> str:
    """Calculate SHA256 hash of the file"""
    hash_sha256 = hashlib.sha256()
    while chunk := file.file.read(8192):  # Read the file in chunks
        hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def serialize_files(file_data):
    file_data["_id"] = str(file_data["_id"])  # Convert ObjectId to string
    return file_data


def save_uploaded_file(file: UploadFile, file_location: str) -> None:
    """Save the file to the specified location"""
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)


@router.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Calculate file hash to check if the file already exists
        file_hash = calculate_file_hash(file)
        print(f"Calculated file hash: {file_hash}")

        # Check if the file hash already exists in the database
        existing_file = fileDB.find_one({"file_hash": file_hash})
        print(f"Existing file found: {existing_file}")

        if existing_file:
            # If the file already exists, return the existing file's URL and info
            existing_file["_id"] = str(existing_file["_id"])  # Convert ObjectId to string
            return {
                "status": "file_exists",
                "message": "The file already exists with the same content.",
                "file_location": existing_file['location'],
                "file_info": existing_file
            }, status.HTTP_200_OK  # Return 200 OK if the file exists

        # Handle file type by extension (allow only audio file types)
        file_extension = file.filename.split('.')[-1].lower()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        # Generate file location path
        file_location = f"static/{file_hash}_{timestamp}_{file.filename}"

        if file_extension in ['mp3', 'wav', 'ogg', 'flac']:  # Audio file extensions
            # If it's an audio file, save it directly
            save_uploaded_file(file, file_location)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only audio files are allowed."
            )

        # Prepare file info to store in MongoDB
        file_info = {
            "filename": file.filename,
            "location": file_location,
            "uploaded_at": timestamp,
            "file_hash": file_hash
        }

        # Insert file info into the database
        result = fileDB.insert_one(file_info)
        print(f"File info inserted: {result.inserted_id}")

        # Add the inserted _id to file_info
        file_info["_id"] = str(result.inserted_id)  # Convert ObjectId to string

        return {
            "status": "success",
            "file_info": file_info
        }, status.HTTP_201_CREATED  # 201 Created for successful file upload

    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Log the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in file upload: {str(e)}"
        )


@router.get('/showfiles')
def show_files():
    files = list(fileDB.find())
    # Serialize files properly (convert ObjectId to string)
    all_files = [serialize_files(file) for file in files]
    return all_files
