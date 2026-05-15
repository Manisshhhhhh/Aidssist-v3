from fastapi import HTTPException, status


class AidssistError(Exception):
    """Base application error for expected Aidssist failures."""


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
