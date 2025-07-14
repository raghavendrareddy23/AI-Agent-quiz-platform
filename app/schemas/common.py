from pydantic import BaseModel
from typing import List, Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    page: int
    limit: int
    total_results: int
    results: List[T]
