from pydantic import BaseModel

class GetTerceroNit(BaseModel):
    nit: str
    fecha: str