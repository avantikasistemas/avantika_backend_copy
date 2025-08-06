from .validator import Validator


class Rules:
    """ Esta clase se encarga de validar los datos de entrada de la API
        y si hay un error, lanza una excepcion """

    val = Validator()

    def __init__(self, path: str, params: dict):
        path_dict = {
            "/get_emails": self.__val_get_emails,
            "/get_tercero_x_nit": self.__val_get_tercero_x_nit,
            "/consultar_cotizacion": self.__val_consultar_cotizacion,
            "/guardar_seguimiento": self.__val_guardar_seguimiento,
        }
        # Se obtiene la funcion a ejecutar
        func = path_dict.get(path, None)
        if func:
            # Se ejecuta la funcion para obtener las reglas de validacion
            validacion_dict = func(params)

            # Se valida la datas
            self.val.validacion_datos_entrada(validacion_dict)

    def __val_get_emails(self, params):
        validacion_dict = [
            {
                "tipo": "date",
                "campo": "fecha de inicio",
                "valor": params["start_date"],
                "obligatorio": False,
            },
            {
                "tipo": "date",
                "campo": "fecha fin",
                "valor": params["end_date"],
                "obligatorio": False,
            }
        ]
        return validacion_dict

    def __val_get_tercero_x_nit(self, params):
        validacion_dict = [
            {
                "tipo": "string",
                "campo": "nit",
                "valor": params["nit"],
                "obligatorio": True,
            },
            {
                "tipo": "string",
                "campo": "fecha",
                "valor": params["fecha"],
                "obligatorio": False,
            }
        ]
        return validacion_dict

    def __val_consultar_cotizacion(self, params):
        validacion_dict = [
            {
                "tipo": "string",
                "campo": "número de cotización",
                "valor": params["numero_cotizacion"],
                "obligatorio": True,
            }
        ]
        return validacion_dict

    def __val_guardar_seguimiento(self, params):
        validacion_dict = [
            {
                "tipo": "string",
                "campo": "cotizacion",
                "valor": params["cotizacion"],
                "obligatorio": True,
            },
            {
                "tipo": "string",
                "campo": "fecha programación",
                "valor": params["fecha_programacion"],
                "obligatorio": True,
            },
            {
                "tipo": "string",
                "campo": "usuario",
                "valor": params["usuario"],
                "obligatorio": True,
            },
            {
                "tipo": "int",
                "campo": "tipo seguimiento",
                "valor": params["tipo_seguimiento"],
                "obligatorio": True,
            },
            {
                "tipo": "string",
                "campo": "contacto",
                "valor": params["contacto"],
                "obligatorio": False,
            }
        ]
        return validacion_dict
