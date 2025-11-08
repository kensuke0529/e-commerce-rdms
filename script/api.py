"""
Main Entry Point for RDMS AI SQL Agent API Server
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

# Enable LangSmith tracing for LangChain components
from .langsmith_config import setup_langsmith

from .sql_generator.ai_sql import AISQLRunner
from .sql_generator.graph import run_sql_agent
from .sql_generator.ai_helpers import format_results_for_api
from .chatbot.customer_chatbot import chatbot

# Initialize LangSmith tracing
setup_langsmith()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "test")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
plain_password = "test_pass"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Models
class QueryRequest(BaseModel):
    prompt: str


class QueryResponse(BaseModel):
    status: str
    question_type: Optional[str] = None
    prompt: str
    sql_query: Optional[str] = None
    data: Optional[list] = None
    analysis: Optional[str] = None
    total_results: Optional[int] = None
    error: Optional[str] = None
    message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    message: str


class ProfileResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ChatRequest(BaseModel):
    prompt: str
    max_attempts: Optional[int] = 5


class ChatResponse(BaseModel):
    answer: str
    status: str = "success"
    error: Optional[str] = None


fake_db = None


def get_fake_db():
    global fake_db
    if fake_db is None:
        fake_db = {
            "ken": {
                "username": "ken_test",
                "full_name": "ken uma",
                "email": "dus49029@gmail.com",
                "hashed_password": pwd_context.hash(plain_password),
            }
        }
    return fake_db


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode.update(
        {"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str):
    user = get_fake_db().get(username)
    return (
        user
        if user and pwd_context.verify(password, user["hashed_password"])
        else False
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if (username := payload.get("sub")) is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception


# FastAPI App
app = FastAPI(
    title="RDMS AI SQL API",
    description="API for AI-powered SQL analysis of e-commerce data",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Find static directory - works in both localhost and Render
# Try multiple possible paths
possible_static_paths = [
    os.path.join(os.path.dirname(__file__), "..", "static"),
    os.path.join(os.path.dirname(__file__), "..", "..", "static"),
    os.path.join(os.getcwd(), "static"),
    os.path.join("/app", "static"),  # Docker/Render path
]

static_dir = None
for path in possible_static_paths:
    if os.path.exists(path) and os.path.isdir(path):
        static_dir = path
        break

if static_dir:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"Static files mounted from: {static_dir}")
else:
    print(f"Warning: Static directory not found. Tried: {possible_static_paths}")

# Initialize AI runner with logging
print("=" * 60)
print("Initializing RDMS AI SQL Agent")
print("=" * 60)
print(f"Current working directory: {os.getcwd()}")
print(f"Script directory: {os.path.dirname(__file__)}")
print(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")

# Check critical directories
critical_dirs = ["static", "sql", "data", "documents"]
for dir_name in critical_dirs:
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", dir_name),
        os.path.join(os.getcwd(), dir_name),
        os.path.join("/app", dir_name),
    ]
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✓ {dir_name} directory found at: {path}")
            found = True
            break
    if not found:
        print(f"⚠ {dir_name} directory not found. Tried: {possible_paths}")

print("=" * 60)

# Debug: Check database environment variables (without exposing passwords)
print("Database Configuration Check:")
db_vars = {
    "DB_HOST": os.getenv("DB_HOST", "NOT_SET"),
    "DB_PORT": os.getenv("DB_PORT", "NOT_SET"),
    "DB_NAME": os.getenv("DB_NAME", "NOT_SET"),
    "DB_USER": os.getenv("DB_USER", "NOT_SET"),
    "DB_PASSWORD": "***SET***" if os.getenv("DB_PASSWORD") else "NOT_SET"
}
for key, value in db_vars.items():
    print(f"  {key}: {value}")
print("=" * 60)

# Lazy initialization - only create when needed to speed up startup
_ai_runner = None

def get_ai_runner():
    """Get or create the AI runner instance (lazy initialization)."""
    global _ai_runner
    if _ai_runner is None:
        print("Initializing AI Runner (lazy)...")
        _ai_runner = AISQLRunner()
        print("✓ AI Runner initialized")
    return _ai_runner

print("✓ AI Runner will be initialized on first use (lazy loading)")
print("=" * 60)


# Endpoints
@app.post("/token", response_model=TokenResponse, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return JWT access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login"
        )
    return TokenResponse(
        access_token=create_access_token({"sub": user["username"]}), token_type="bearer"
    )


@app.post("/analyze", response_model=QueryResponse, tags=["Analysis"])
def analyze_query(request: QueryRequest, current_user: str = Depends(get_current_user)):
    """Process a natural language query and return SQL analysis results."""
    question_type = None
    try:
        # Get AI runner (lazy initialization)
        ai_runner = get_ai_runner()
        
        # Try to classify the prompt
        try:
            question_type = ai_runner.classification_prompt(request.prompt)
        except Exception as e:
            # If classification fails, default to SQL (safer for data queries)
            question_type = "sql"
            print(f"Classification failed, defaulting to SQL: {e}")
        
        if question_type == "conversational":
            response = ai_runner.get_conversational_response(request.prompt)
            return QueryResponse(
                status="success",
                question_type="conversational",
                prompt=request.prompt,
                analysis=response,
                sql_query=None,
                data=None,
            )

        # Handle SQL queries (default path if classification is not "conversational")
        result = run_sql_agent(request.prompt, ai_runner, max_retries=2)

        final_response = result.get("final_response")
        sql_query = result.get("sql_query")
        sql_results = result.get("sql_results")

        if not final_response:
            # Error case - SQL execution failed
            error_message = result.get("error_message", "Unknown error")
            print(f"SQL Agent error: {error_message}")
            return QueryResponse(
                status="error",
                question_type="sql",
                prompt=request.prompt,
                error=error_message,
                message=error_message,
                sql_query=sql_query,
            )

        # Ensure we have a response (fallback if empty)
        if not final_response or final_response.strip() == "":
            final_response = "Query executed successfully, but no analysis was generated."

        # Success case - format data for API
        formatted_data = None
        if sql_results:
            formatted_data = format_results_for_api(sql_results)

        return QueryResponse(
            status="success",
            question_type="sql",
            prompt=request.prompt,
            sql_query=sql_query,
            data=formatted_data,
            analysis=final_response,
            total_results=len(formatted_data) if formatted_data else 0,
        )

    except Exception as e:
        # Ensure question_type is set even in error cases
        # If it was SQL-related, preserve that, otherwise assume SQL (safer default)
        error_question_type = question_type if question_type else "sql"
        
        # Provide more detailed error messages
        error_str = str(e)
        if "connection" in error_str.lower() or "database" in error_str.lower():
            error_message = f"Database connection error: {error_str}. Please check database configuration."
        elif "OPENAI_API_KEY" in error_str or "openai" in error_str.lower():
            error_message = f"OpenAI API error: {error_str}. Please check API key configuration."
        else:
            error_message = f"An error occurred while processing your request: {error_str}"

        print(f"API Error: {error_message}")
        import traceback
        traceback.print_exc()

        return QueryResponse(
            status="error",
            question_type=error_question_type,
            prompt=request.prompt,
            error=error_str,
            message=error_message,
        )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint with database connectivity test."""
    # Check if database environment variables are set
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    if not all([db_host, db_port, db_name, db_user, db_password]):
        missing = []
        if not db_host: missing.append("DB_HOST")
        if not db_port: missing.append("DB_PORT")
        if not db_name: missing.append("DB_NAME")
        if not db_user: missing.append("DB_USER")
        if not db_password: missing.append("DB_PASSWORD")
        return HealthResponse(
            status="degraded",
            message=f"API is running but database environment variables are missing: {', '.join(missing)}. Please check Render dashboard configuration."
        )
    
    try:
        # Test database connection
        from .sql_generator.sql_via_python import query_executor
        test_db = query_executor("SELECT 1")
        test_db.connect_to_db()
        test_db.close()
        return HealthResponse(status="healthy", message="API is running and database is connected")
    except Exception as e:
        return HealthResponse(
            status="degraded", 
            message=f"API is running but database connection failed: {str(e)}"
        )


@app.get("/profile", response_model=ProfileResponse, tags=["User"])
async def read_profile(username: str = Depends(get_current_user)):
    """Get current user profile information."""
    return ProfileResponse(message=f"Welcome {username}!")


@app.get("/", tags=["Frontend"])
async def read_root():
    """Serve the frontend interface."""
    # Find index.html - works in both localhost and Render
    possible_index_paths = [
        os.path.join(os.path.dirname(__file__), "..", "static", "index.html"),
        os.path.join(os.path.dirname(__file__), "..", "..", "static", "index.html"),
        os.path.join(os.getcwd(), "static", "index.html"),
        os.path.join("/app", "static", "index.html"),  # Docker/Render path
    ]
    
    for path in possible_index_paths:
        if os.path.exists(path):
            return FileResponse(path)
    
    # Fallback: return error if not found
    raise HTTPException(
        status_code=404,
        detail=f"index.html not found. Tried paths: {possible_index_paths}"
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
def chat_endpoint(request: ChatRequest, current_user: str = Depends(get_current_user)):
    """Chat with the customer service chatbot."""
    try:
        answer, chat_response, response = chatbot(
            request.prompt, max_attempts=request.max_attempts
        )
        return ChatResponse(
            answer=answer or "I apologize, but I couldn't generate a response.",
            status="success",
        )
    except Exception as e:
        return ChatResponse(answer="", status="error", error=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Use PORT from environment (Render sets this) or default to 8011
    port = int(os.getenv("PORT", 8011))
    uvicorn.run(app, host="0.0.0.0", port=port)
