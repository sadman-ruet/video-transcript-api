from fastapi import APIRouter, Depends, HTTPException
from schemas import user
from database import userDB, chatDB
from schemas.user import User, UserInfo
from pymongo import MongoClient

router = APIRouter(
    tags=["User"],
    prefix="/user"
)

def serialize_user(user_data):
    user_data["_id"] = str(user_data["_id"])  # Convert ObjectId to string
    return user_data


@router.get('/')
def index():
    # Find all users in the userDB collection
    all_users_cursor = userDB.find({})

    # Serialize the users into a list of dictionaries
    all_users = [serialize_user(user) for user in all_users_cursor]

    # Return the list of users
    return {"users": all_users}

@router.post('/')
def userCreate(request: User):
    # Check if user already exists
    existing_user = userDB.find_one({"name": request.name, "email": request.email})
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists!")
    
    # Create new user document
    user_data = {
        "name": request.name,
        "email": request.email,
        "username": request.username
    }
    
    # Insert new user into MongoDB collection
    userDB.insert_one(user_data)
    
    return {"Message": f"User {request.name} successfully inserted into user collection."}

# Get user info endpoint
@router.get('/{username}')
def userGet(username: str):
    # Query the database for the user by username
    user_info = userDB.find_one({"username": username})
    
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return user data as per the UserInfo response model
    return {
        "name": user_info['name'],
        "email": user_info['email']
    }

@router.put('/{username}')
def userUpdate(username: str, request: user.User):
    # Find the existing user by username
    user_info = userDB.find_one({"username": username})
    
    if not user_info:
        # If user doesn't exist, raise HTTPException
        raise HTTPException(status_code=404, detail=f"User {username} not found")
    
    # Prepare the updated user information
    updated_user_info = {
        "name": request.name,
        "email": request.email,
        "username": request.username
    }

    # Perform the update in MongoDB
    result = userDB.update_one(
        {"username": username},
        {"$set": updated_user_info}
    )
    
    # Check if the update was acknowledged
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail=f"Failed to update user {username}")

    # Return success message
    return {"Message": f"User {username} successfully updated in user collection."}

@router.delete('/{username}')
def userDelete(username: str):
    # Find the user by username
    user_info = userDB.find_one({"username": username})
    
    if not user_info:
        # If user doesn't exist, raise HTTPException
        raise HTTPException(status_code=404, detail=f"User {username} not found")
    
    # Perform the deletion in MongoDB
    result = userDB.delete_one({"username": username})
    
    # Check if the deletion was acknowledged
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail=f"Failed to delete user {username}")

    # Return success message
    return {"Message": f"User {username} successfully deleted from user collection."}



