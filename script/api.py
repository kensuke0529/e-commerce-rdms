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
from langsmith_config import setup_langsmith

from sql_generator.ai_sql import AISQLRunner
from sql_generator.graph import run_sql_agent
from sql_generator.ai_helpers import format_results_for_api
from chatbot.customer_chatbot import chatbot

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

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize AI runner lazily (like chatbot) - will be created on first use
_ai_runner = None

def get_ai_runner():
    """Get or create AISQLRunner instance (lazy initialization like chatbot)."""
    global _ai_runner
    if _ai_runner is None:
        try:
            _ai_runner = AISQLRunner()
            print("✓ AISQLRunner initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize AISQLRunner: {e}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise so the endpoint can handle it
    return _ai_runner


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
        # Get AI runner (lazy initialization, like chatbot)
        try:
            ai_runner = get_ai_runner()
        except Exception as e:
            return QueryResponse(
                status="error",
                question_type="sql",
                prompt=request.prompt,
                error="AI SQL Runner initialization failed",
                message=f"Failed to initialize AI SQL Runner: {str(e)}. Please check server logs and ensure all environment variables (OPENAI_API_KEY, DB_*) are set correctly.",
            )
        
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

        # Format data for API
        formatted_data = None
        if sql_results:
            formatted_data = format_results_for_api(sql_results)

        # If no final_response but we have SQL results, generate AI analysis
        if not final_response and sql_results:
            print("Warning: Graph didn't return final_response, generating analysis from results")
            try:
                # Pass SQL query so AI can see what was executed
                final_response = ai_runner.analyze_sql_results(
                    request.prompt, 
                    sql_results,
                    sql_query=sql_query
                )
            except Exception as e:
                print(f"Error generating fallback analysis: {e}")
                # Last resort: create a simple response
                final_response = f"I've retrieved the data for your question: '{request.prompt}'. The query executed successfully and returned {len(formatted_data) if formatted_data else 0} results."

        if not final_response:
            # Error case - SQL execution failed or no results
            error_message = result.get("error_message", "Unknown error")
            return QueryResponse(
                status="error",
                question_type="sql",
                prompt=request.prompt,
                error=error_message,
                message=error_message,
                sql_query=sql_query,
            )

        # Success case - return with AI analysis
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
        
        # Log the full error for debugging (like chatbot does)
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in analyze_query: {str(e)}")
        print(f"Traceback: {error_trace}")

        # Return user-friendly error message (consistent with chatbot pattern)
        error_message = str(e)
        if "database" in error_message.lower() or "connection" in error_message.lower():
            user_message = "Database connection error. Please check that the database is running and accessible."
        elif "openai" in error_message.lower() or "api key" in error_message.lower():
            user_message = "OpenAI API error. Please check your API key and ensure you have available credits."
        else:
            user_message = f"An error occurred while processing your request: {error_message}"

        return QueryResponse(
            status="error",
            question_type=error_question_type,
            prompt=request.prompt,
            error=error_message,
            message=user_message,
        )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", message="API is running")


@app.get("/diagnostics", tags=["Health"])
def diagnostics():
    """Diagnostic endpoint to check configuration and connections."""
    diagnostics_info = {
        "api_status": "running",
        "environment_variables": {
            "DB_HOST": "✓" if os.getenv("DB_HOST") else "✗ Missing",
            "DB_PORT": os.getenv("DB_PORT", "✗ Missing"),
            "DB_NAME": "✓" if os.getenv("DB_NAME") else "✗ Missing",
            "DB_USER": "✓" if os.getenv("DB_USER") else "✗ Missing",
            "DB_PASSWORD": "✓" if os.getenv("DB_PASSWORD") else "✗ Missing",
            "OPENAI_API_KEY": "✓" if os.getenv("OPENAI_API_KEY") else "✗ Missing",
            "SECRET_KEY": "✓" if os.getenv("SECRET_KEY") else "⚠ Using default",
        },
        "database_connection": "unknown",
        "openai_connection": "unknown",
    }
    
    # Test database connection
    try:
        from sql_generator.sql_via_python import query_executor
        test_query = query_executor("SELECT 1")
        test_query.connect_to_db()
        test_query.cur.close()
        test_query.conn.close()
        diagnostics_info["database_connection"] = "✓ Connected"
    except Exception as e:
        diagnostics_info["database_connection"] = f"✗ Error: {str(e)}"
    
    # Test OpenAI connection (just check if key is valid format)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        if openai_key.startswith("sk-") and len(openai_key) > 20:
            diagnostics_info["openai_connection"] = "✓ Key format valid"
        else:
            diagnostics_info["openai_connection"] = "⚠ Key format may be invalid"
    else:
        diagnostics_info["openai_connection"] = "✗ No key provided"
    
    return diagnostics_info


@app.get("/profile", response_model=ProfileResponse, tags=["User"])
async def read_profile(username: str = Depends(get_current_user)):
    """Get current user profile information."""
    return ProfileResponse(message=f"Welcome {username}!")


@app.get("/", tags=["Frontend"])
async def read_root():
    """Serve the frontend interface."""
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
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

    uvicorn.run(app, host="0.0.0.0", port=8011)
