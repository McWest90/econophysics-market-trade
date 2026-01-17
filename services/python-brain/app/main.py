from fastapi import FastAPI

app = FastAPI(title="QuantCore Brain", version="1.0")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "The Brain is active 🧠"}

@app.get("/physics/alpha")
def check_alpha():
    return {"market": "MOEX", "alpha_const": 0.44}