from pydantic import BaseModel, ConfigDict, field_validator


class Geometry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    coordinates: list[float]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, value: list[float]) -> list[float]:
        if len(value) < 2:
            raise ValueError("coordinates must contain at least [longitude, latitude]")

        lng, lat = float(value[0]), float(value[1])
        if not -180 <= lng <= 180:
            raise ValueError("longitude must be between -180 and 180")
        if not -90 <= lat <= 90:
            raise ValueError("latitude must be between -90 and 90")

        return [lng, lat]
