from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {'message':'FastApi is working'}
