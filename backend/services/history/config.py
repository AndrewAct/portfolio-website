import os

def get_cors_origins():
    ENV = os.getenv("ENV", "development")
    return (
        ["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost",]
        if ENV == "development"
        else ["https://andrewcee.io"]
    )