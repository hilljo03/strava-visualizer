from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}
