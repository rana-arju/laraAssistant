from fastapi.responses import JSONResponse
from fastapi import status
from typing import Any, Optional


def send_response(
    status_code: int = status.HTTP_200_OK,
    message: str = "Success",
    data: Optional[Any] = None,
) -> JSONResponse:
    """
    Returns a standardized JSON response matching Express sendResponse pattern.
    
    Usage:
    return send_response(
        status_code=200,
        message="OTP verified successfully", 
        data=result
    )
    
    Response format:
    {
        "statusCode": 200,
        "message": "OTP verified successfully",
        "data": { ... }
    }
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "data": data,
        },
    )


def send_error(
    status_code: int = status.HTTP_400_BAD_REQUEST,
    message: str = "An error occurred",
    data: Optional[Any] = None,
) -> JSONResponse:
    """
    Standardized error response following same wrapper pattern.
    
    Usage:
    return send_error(
        status_code=400,
        message="Invalid request data",
        data={"field": "email", "error": "Invalid format"}
    )
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "data": data,
        },
    )