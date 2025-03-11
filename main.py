from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import model, user, file

app = FastAPI()  # Enable FastAPI debug mode

# Serve static files (like images, stylesheets) under the '/static' path
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(user.router)
app.include_router(file.router)
app.include_router(model.router)

@app.get("/")
def root():
    return FileResponse("index.html")

