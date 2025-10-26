from fastapi import FastAPI
from pydantic import BaseModel
from ai_sql import AISQLRunner
import uvicorn

class Item(BaseModel):
    prompt: str 
    query: str 
    data: str
    
app = FastAPI(title="RDMS AI SQL API", description="API for AI-powered SQL analysis of e-commerce data")

# Create a single AI instance that persists across requests
ai_runner = AISQLRunner()

@app.post("/analyze")
def ai_chat(item: Item):
    response_data = ai_runner.ask_ai_api(prompt=item.prompt)
    
    return response_data

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)