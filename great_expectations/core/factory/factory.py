from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Factory(ABC, Generic[T]):
    """
    Responsible for basic CRUD operations on collections of GX domain objects.
    """

    @abstractmethod
    def add(self, obj: T) -> T:
        pass

    @abstractmethod
    def delete(self, obj: T) -> T:
        pass

    @abstractmethod
    def get(self, name: str) -> T:
        pass
