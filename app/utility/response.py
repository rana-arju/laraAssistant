# app/utils/response.py
from fastapi.responses import JSONResponse
from fastapi import status

def send_response(
    status_code: int = status.HTTP_200_OK,
    message: str = "Success",
    data: any = None,
):
    """
    Returns a standardized JSON response.
    Similar to: sendResponse(res, { statusCode, message, data })
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
    errors: any = None,
):
    """
    Standardized error response.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "errors": errors,
        },
    )
