from fastapi import FastAPI

app = FastAPI(title="Lenny Growth Assistant API")

@app.get("/")
def read_root():
    return {"Hello": "World"}
