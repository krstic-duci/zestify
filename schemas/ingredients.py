from pydantic import BaseModel, ConfigDict, Field, field_validator


class IngredientsRequest(BaseModel):
    """Request payload for ingredients processing.

    - recipes_text: required, trimmed, with a sensible minimum length
    - have_at_home: optional, blank strings coerced to None
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    recipes_text: str = Field(
        min_length=10, description="Raw recipes + ingredients text"
    )
    have_at_home: str | None = Field(
        default=None, description="Items already available at home"
    )

    @field_validator("have_at_home", mode="before")
    @classmethod
    def blank_to_none(cls, v: str | None) -> str | None:
        if isinstance(v, str) and not v.strip():
            return None
        return v
