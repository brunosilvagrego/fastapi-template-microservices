import pydantic


class BaseModel(pydantic.BaseModel):
    """Base model for all schemas. General configurations may be added here."""


class NonEmptyModel(BaseModel):
    @pydantic.model_validator(mode="after")
    def at_least_one_field(self):
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field must be provided")
        return self
