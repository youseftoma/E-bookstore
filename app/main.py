import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import IntegrityError

from .routes import user, book, orderitem, order, auth, comments_likes_system
from .limiter import limiter

# future plan 
# 1- add reports 
# 2- add ai-chatbot

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

def start():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)

# Register a proper handler for RateLimitExceeded
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Try again later."},
    )

# Global handler for database errors
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database integrity error", "code": 1001}
    )

# Catch-all global handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # You still see the stack trace in terminal/logs
    print(f"Unexpected error: {exc}")

    # User gets a clean JSON response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "code": 9999}
    )

@app.get("/")
@limiter.limit("5/minute")
def index(request: Request):
    return {"message":"hello, world"}

app.include_router(user.route)
app.include_router(book.route)
app.include_router(comments_likes_system.route)
app.include_router(order.route)
app.include_router(orderitem.route)
app.include_router(auth.route)
app.include_router(user.adminroute)
app.include_router(user.banroute)
app.include_router(book.adminroute)
app.include_router(order.adminroute)
app.include_router(orderitem.adminroute)

if __name__ == "__main__":
    start()
