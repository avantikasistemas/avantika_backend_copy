from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Schemas.Cotizacion.get_tercero_x_nit import GetTerceroNit
from Schemas.Cotizacion.consultar_cotizacion import ConsultarCotizacion
from Class.Cotizacion import Cotizacion
from Utils.decorator import http_decorator
from Config.db import get_db

cotizacion_router = APIRouter()

@cotizacion_router.post('/get_tercero_x_nit', tags=["Cotización"], response_model=dict)
@http_decorator
def get_tercero_x_nit(request: Request, getTerceroNit: GetTerceroNit, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).get_tercero_x_nit(data)
    return response

@cotizacion_router.post('/consultar_cotizacion', tags=["Cotización"], response_model=dict)
@http_decorator
def consultar_cotizacion(request: Request, consultarCotizacion: ConsultarCotizacion, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).consultar_cotizacion(data)
    return response

@cotizacion_router.post('/guardar_cotizacion', tags=["Cotización"], response_model=dict)
@http_decorator
def guardar_cotizacion(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).guardar_cotizacion(data)
    return response

@cotizacion_router.post('/actualizar_cotizacion', tags=["Cotización"], response_model=dict)
@http_decorator
def actualizar_cotizacion(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).actualizar_cotizacion(data)
    return response

@cotizacion_router.post('/cargar_datos_cotizacion', tags=["Cotización"], response_model=dict)
@http_decorator
def cargar_datos_cotizacion(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).cargar_datos_cotizacion(data)
    return response

@cotizacion_router.post('/get_terceros', tags=["Cotización"], response_model=dict)
@http_decorator
def get_terceros(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).get_terceros(data)
    return response

@cotizacion_router.post('/calcular_dia_habil', tags=["Cotización"], response_model=dict)
@http_decorator
def calcular_dia_habil(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).calcular_dia_habil(data)
    return response

@cotizacion_router.post('/obtener_contactos', tags=["Cotización"], response_model=dict)
@http_decorator
def obtener_contactos(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).obtener_contactos(data)
    return response

@cotizacion_router.post('/guardar_seguimiento_desde_principal', tags=["Cotización"], response_model=dict)
@http_decorator
def guardar_seguimiento_desde_principal(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Cotizacion(db).guardar_seguimiento_desde_principal(data)
    return response
