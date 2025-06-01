import uuid
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class LocationModel(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    driving_time_to_target_seconds: Optional[int] = None # Stores temporary calculation result
    notes: Optional[str] = None
    enrichment_data: Optional[Dict] = Field(default_factory=dict) # For future data like population, etc.

    class Config:
        # Pydantic V2 config
        from_attributes = True # Formerly orm_mode

class LocationCreate(BaseModel): # For creating new locations, ID is not needed
    name: str
    address: str
    notes: Optional[str] = None
    latitude: Optional[float] = None # Allow setting lat/lng directly if known
    longitude: Optional[float] = None

class LocationUpdate(BaseModel): # For updating, all fields are optional
    name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    enrichment_data: Optional[Dict] = None
