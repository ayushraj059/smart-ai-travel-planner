from pydantic import BaseModel
from typing import Optional


class Place(BaseModel):
    name: str
    city: str
    country: str
    category: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[str] = None
    formatted_address: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None


class PlaceResponse(BaseModel):
    city: str
    category: str
    name: str
    country: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[str] = None
    formatted_address: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None


class ExploreResponse(BaseModel):
    city: str
    total: int
    items: list[PlaceResponse]


class PlacesResponse(BaseModel):
    city: str
    category: str
    total: int
    items: list[PlaceResponse]
