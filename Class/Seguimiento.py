from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime
import traceback


class Seguimiento:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)

    # Funcion para buscar una cotización.    
    def buscar_cotizacion(self, data: str):
        
        cotizacion = data["cotizacion"].strip()
        contactos = list()
        resultado_seguimiento = None
        
        try:
            # Acá revisamos si existe o no la cotización.
            data_cotizacion = self.querys.check_if_cotizacion_exists(cotizacion)
            if not data_cotizacion:
                raise CustomException("No se encontró la cotización.")
            
            data_seguimiento = self.querys.get_data_seguimiento(cotizacion)
            if data_seguimiento:
                resultado_seguimiento = data_seguimiento["resultado_seguimiento"]
            
            historia_seguimiento = self.querys.get_historia_seguimiento(cotizacion)
            
            if data_cotizacion:
                contactos = self.querys.get_contactos_cotizacion(data_cotizacion["nit"])
            
            response = {
                "data_cotizacion": data_cotizacion,
                "historia_seguimiento": historia_seguimiento,
                "contactos": contactos,
                "resultado_seguimiento": resultado_seguimiento,
                "data_seguimiento": data_seguimiento
            }

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", response)

        except Exception as e:
            print(f"{e}")
            print(traceback.format_exc())
            raise CustomException(f"{e}")

    # Api que realiza el guardado de un seguimiento de una cotización. 
    def guardar_seguimiento(self, data: dict):

        # Formateamos la fecha de programación.
        data["fecha_programacion"] = datetime.strptime(
            data["fecha_programacion"], 
            "%Y-%m-%dT%H:%M"
        ) if data["fecha_programacion"] else None

        try:
            # Acá revisamos si existe o no la cotización.
            self.querys.check_if_cotizacion_exists(data["cotizacion"])
            
            # Acá revisamos si la cotización ya tiene un seguimiento creado
            # desde el correo.
            data_segui_coti = self.querys.check_seguimiento_coti_correo_exists(
                data["cotizacion"])
            
            data_segui_coti_id = data_segui_coti["id"]
            
            # Revisamos si el seguimiento ya existe.
            segui = self.querys.check_seguimiento_exists(data["cotizacion"])
            segui_progra_id = segui.id if segui else None
            if not segui:
                # Guardamos el seguimiento de la cotización.
                segui_progra_id = self.querys.guardar_seguimiento(
                    data, data_segui_coti_id)
            
            # Guardamos la historia del seguimiento.
            self.querys.guardar_historia_seguimiento(data, segui_progra_id)

            # Retornamos la información.
            return self.tools.output(200, "Seguimiento guardado.")

        except Exception as e:
            print(f"{e}")
            print(traceback.format_exc())  
            raise CustomException(f"{e}")

    # Api que actualiza el resultado de una llamada.
    def actualizar_resultado_llamada(self, data: dict):
        try:

            # Verificamos si el seguimiento existe.
            self.querys.check_seguimiento_id(data)

            # Actualizamos el resultado de la llamada.
            result_data = self.querys.actualizar_resultado_llamada(data)

            # Retornamos la información.
            return self.tools.output(200, "Resultado de llamada actualizado.", result_data)

        except Exception as e:
            print(f"{e}")
            print(traceback.format_exc())
            raise CustomException(f"{e}")

    # Api que guarda la información de no adjudicación.
    def guardar_no_adjudicacion(self, data: dict):
        try:

            # Actualizamos la información de no adjudicación.
            data_segui = self.querys.guardar_no_adjudicacion(data)

            # Retornamos la información.
            return self.tools.output(200, "Información guardada con éxito.", data_segui)

        except Exception as e:
            print(f"{e}")
            print(traceback.format_exc())
            raise CustomException(f"{e}")

    # Api que guarda la información de adjudicación.
    def guardar_en_estudio(self, data: dict):
        try:

            # Actualizamos la información de adjudicación.
            data_segui = self.querys.guardar_en_estudio(data)

            # Retornamos la información.
            return self.tools.output(200, "Información guardada con éxito.", data_segui)

        except Exception as e:
            print(f"{e}")
            print(traceback.format_exc())
            raise CustomException(f"{e}")
