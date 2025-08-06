import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from Config.db import BASE, engine
from Middleware.get_json import JSONMiddleware
from Router.Graph import graph_router
from Router.Cotizacion import cotizacion_router
from Router.Parametros import parametros_router
from Router.Seguimiento import seguimiento_router
# from pathlib import Path


# route = Path.cwd()
app = FastAPI()
app.title = "Avantika Cotizaciones"
app.version = "0.0.1"

# # Sirve la carpeta "assets" en la ruta "/assets"
# app.mount("/assets", StaticFiles(directory=f"{route}/assets"), name="assets")
# app.mount("/Uploads", StaticFiles(directory=f"{route}/Uploads"), name="Uploads")
app.add_middleware(JSONMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes; para producción, especifica los orígenes permitidos.
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos; puedes especificar los métodos permitidos.
    allow_headers=["*"],  # Permitir todos los encabezados; puedes especificar los encabezados permitidos.
)
app.include_router(graph_router)
app.include_router(cotizacion_router)
app.include_router(seguimiento_router)
app.include_router(parametros_router)

BASE.metadata.create_all(bind=engine)