from Utils.tools import Tools, CustomException
from Utils.querys import Querys

class Parametros:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)

    def get_tipos_estado(self):
        """ Api que realiza la consulta de los estados. """

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.get_tipos_estado()

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos)

        except Exception as e:
            print(f"Error al obtener información de tercero: {e}")
            raise CustomException("Error al obtener información de tercero.")

    def tipo_seguimientos(self):
        """ Api que realiza la consulta de los estados. """

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.tipo_seguimientos()

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos)

        except Exception as e:
            print(f"Error al obtener información de tercero: {e}")
            raise CustomException("Error al obtener información de tercero.")

    def tipo_resultado_llamada(self):
        """ Api que realiza la consulta de los estados. """

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.tipo_resultado_llamada()

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos)

        except Exception as e:
            print(f"Error al obtener información de tercero: {e}")
            raise CustomException("Error al obtener información de tercero.")

    def motivos_no_adjudicacion(self):
        """ Api que realiza la consulta de los estados. """

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.motivos_no_adjudicacion()

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos)

        except Exception as e:
            print(f"Error al obtener información de tercero: {e}")
            raise CustomException("Error al obtener información de tercero.")
