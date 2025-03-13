import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import model, user, file
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORSMiddleware to allow requests from the frontend (localhost:63342)
origins = [
    "http://localhost:49950",  # Frontend origin (your local dev environment)
    "http://127.0.0.1:8000",   # Backend origin (if applicable)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow frontend URLs to access the backend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (if needed)
)

# Serve static files (like images, stylesheets) under the '/static' path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers for other parts of the app
app.include_router(user.router)
app.include_router(file.router)
app.include_router(model.router)

@app.get("/")
def root():
    # Ensure the path to 'index.html' is correct, you can adjust the path as needed
    index_path = os.path.join(os.path.dirname(__file__), "index.html")

    # Return the index.html file from the correct location
    return FileResponse(index_path)
