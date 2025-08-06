from Utils.tools import Tools
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from Schemas.Graph.get_emails import GetEmails
from Class.Graph import Graph
from Utils.decorator import http_decorator
from Config.db import get_db
# from Middleware.jwt_bearer import JWTBearer

tools = Tools()
graph_router = APIRouter()

@graph_router.post('/get_emails', tags=["Emails"], response_model=dict)
@http_decorator
def get_emails(request: Request, getEmails: GetEmails, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Graph(db).get_emails(data)
    return response

@graph_router.post('/actualizar_estado_seguimiento', tags=["Emails"], response_model=dict)
@http_decorator
def actualizar_estado_seguimiento(request: Request, db: Session = Depends(get_db)):
    data = getattr(request.state, "json_data", {})
    response = Graph(db).actualizar_estado_seguimiento(data)
    return response
