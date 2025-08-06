from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Class.Parametros import Parametros
from Utils.decorator import http_decorator
from Config.db import get_db

parametros_router = APIRouter()

@parametros_router.post('/get_tipos_estado', tags=["Parametros"], response_model=dict)
@http_decorator
def get_tipos_estado(request: Request, db: Session = Depends(get_db)):
    response = Parametros(db).get_tipos_estado()
    return response

@parametros_router.post('/tipo_seguimientos', tags=["Parametros"], response_model=dict)
@http_decorator
def tipo_seguimientos(request: Request, db: Session = Depends(get_db)):
    response = Parametros(db).tipo_seguimientos()
    return response

@parametros_router.post('/tipo_resultado_llamada', tags=["Parametros"], response_model=dict)
@http_decorator
def tipo_resultado_llamada(request: Request, db: Session = Depends(get_db)):
    response = Parametros(db).tipo_resultado_llamada()
    return response

@parametros_router.post('/motivos_no_adjudicacion', tags=["Parametros"], response_model=dict)
@http_decorator
def motivos_no_adjudicacion(request: Request, db: Session = Depends(get_db)):
    response = Parametros(db).motivos_no_adjudicacion()
    return response
