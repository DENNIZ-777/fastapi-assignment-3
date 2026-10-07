from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler

from src.common.source_hash import get_all_src_py_files_hash
from src.api import api_router
from src.common.custom_exception import CustomException

app = FastAPI()

app.include_router(api_router)

@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(request: Request, exc: RequestValidationError):
    if any(error.get("type") == "missing" for error in exc.errors()):
        return JSONResponse(
            status_code=422,
            content={"error_code": "ERR_001", "error_msg": "MISSING VALUE"},
        )
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(CustomException)
def handle_custom_exception(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "error_msg": exc.error_message},
    )


@app.get("/")
def get_root():
    return {"message": "Hello from automated deployment!"}


@app.get("/health")
def health_check():
    # 서버 정상 배포 여부를 확인하기 위한 엔드포인트입니다.
    # 본 코드는 수정하지 말아주세요!
    hash = get_all_src_py_files_hash()
    return {
        "status": "ok",
        "hash": hash
    }
