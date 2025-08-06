from pydantic import BaseModel

class ConsultarCotizacion(BaseModel):
    numero_cotizacion: str
