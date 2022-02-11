from fastapi.responses import JSONResponse

from models.exceptions import InvalidField


def invalid_field_exception_handler(request, exc: InvalidField):
    return JSONResponse(status_code=int(f"{exc.code}"), content={"message": f"{exc.message}", "field": f"{exc.field}"})
