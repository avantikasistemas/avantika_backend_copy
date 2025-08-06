from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime, timedelta, timezone
import pytz
from Utils.constants import (
    START_WORK_HOUR, END_WORK_HOUR
)
import traceback
import requests

class Cotizacion:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)
        self.holidays = {
            "2025-03-03", "2025-03-04",
            "2025-03-24", "2025-04-17", "2025-04-18", "2025-05-01", 
            "2025-06-02", "2025-06-23", "2025-06-30", "2025-07-20", 
            "2025-08-07", "2025-08-18", "2025-10-13", "2025-11-03", 
            "2025-11-17", "2025-12-08", "2025-12-25"
        }

    # Función para obtener el tercero por NIT
    def get_tercero_x_nit(self, data: dict):
        """ Api que realiza la consulta del tercero a la base de datos. """

        # Asignamos nuestros datos de entrada a sus respectivas variables
        nit = data["nit"].strip()
        fecha = data.get("fecha", None)

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.get_tercero_x_nit(nit)

            # Calculamos fecha de vencimiento
            fecha_venc = self.calculate_expiry_date(datos, fecha)

            # Agregamos la fecha al json de salida
            datos.update({"fecha_vencimiento": fecha_venc})

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos)

        except Exception as e:
            print(f"Error al obtener información de tercero: {e}")
            raise CustomException("Error al obtener información de tercero.")

    # Función para calcular la fecha de vencimiento de una cotización
    def calculate_expiry_date(self, datos: dict, fecha: any):

        # Retornamos vacío si no hay fecha ni tipo de cliente
        if not fecha or not datos["tipo_cliente"]:
            return ""

        # Convertimos en mayúscula el tipo de cliente
        tipo_cliente = datos["tipo_cliente"].upper()

        # Calculamos los dias adicionales dependiendo del tipo de cliente
        dias_adicionales = 5 if tipo_cliente in [
            "PUBLICO", "ESAL_PUBLICO"] else 2

        # Obtenemos la fecha de vencimiento
        expiry_date = self.add_business_days(fecha, dias_adicionales)

        # Convertimos la fecha en string
        expiry_date_field = expiry_date.strftime("%d-%m-%Y %H:%M:%S")

        # Retornamos la fecha de vencimiento.
        return expiry_date_field

    # Función para agregar días hábiles a una fecha
    def add_business_days(self, start_date, days_to_add):

        fecha_obj = start_date
        current_date = datetime.strptime(fecha_obj, "%d-%m-%Y %H:%M:%S")

        # Si la hora de inicio está fuera del horario laboral, comenzar al siguiente día hábil
        if current_date.time() < START_WORK_HOUR or current_date.time() > END_WORK_HOUR:
            current_date = self.move_to_next_business_day(current_date)

        # Contador de días hábiles agregados
        added_days = 0
        while added_days < days_to_add:
            # Avanza un día
            current_date += timedelta(days=1)
            # Verifica si es un día hábil
            if self.is_business_day(current_date):
                added_days += 1

        # Asegura que la fecha final esté dentro del horario laboral
        if current_date.time() > END_WORK_HOUR:
            current_date = datetime.combine(current_date.date(), START_WORK_HOUR)
        return current_date

    # Función para verificar si un día es hábil
    def is_business_day(self, date):
        # Verifica que no sea sábado, domingo ni un día festivo
        return date.weekday() < 5 and date.strftime("%Y-%m-%d") not in self.holidays

    # Función para pasar al siguiente día hábil
    def move_to_next_business_day(self, date):
        # Pasa al próximo día hábil si el día actual es fuera de horario o no hábil
        while not self.is_business_day(date) or date.time() > END_WORK_HOUR:
            date += timedelta(days=1)
            date = datetime.combine(date, START_WORK_HOUR)
        return date

    # Función para calcular la oportunidad en la entrega
    def calculate_opportunity(self, fecha_entrega, fecha_vencimiento):
        # Convertimos la fecha de vencimiento en tipo datetime para calcular 
        fecha_vencimiento = datetime.strptime(fecha_vencimiento, "%d-%m-%Y %H:%M:%S")
        # Restamos la fecha de entrega menos vencimiento
        diff = fecha_entrega - fecha_vencimiento
        # Retornamos la diferencia
        return diff
 
    # función para calcular los días de entrega
    def calculate_delivery_days(self, fecha_entrega, fecha_hora_correo):
        # Convertimos la fecha del registro elegido en tipo datetime para calcular
        fecha_entrada = datetime.strptime(fecha_hora_correo, "%d-%m-%Y %H:%M:%S")
        fecha_entrada = fecha_entrada.astimezone(
            pytz.timezone('America/Bogota')).replace(tzinfo=None)
        # Restamos la fecha de entrega menos vencimiento
        diff = fecha_entrega - fecha_entrada
        # Retornamos la diferencia
        return diff

    # Api que busca una cotización.    
    def consultar_cotizacion(self, data: dict):
        
        # Asignamos los datos de entrada a variables 
        num_cot = data["numero_cotizacion"].strip()
        fecha_hora_correo = data.get("fecha", None)
        fecha_vencimiento = data.get("fecha_vencimiento", None)

        # Inicializamos otras variables
        dias_oportunidad = 0
        dias_entrega = 0
        response = dict()

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.consultar_cotizacion(num_cot)

            if datos:
                fecha_entrega = datos[0]["fecha_hora_entrega"]

                # Calcular la oportunidad en la entrega
                if fecha_vencimiento:
                    diff_dias_oportunidad = self.calculate_opportunity(fecha_entrega, fecha_vencimiento)
                    dias_oportunidad = diff_dias_oportunidad.days

                # Calcular los días de entrega
                if fecha_hora_correo:
                    diff_dias_entrega = self.calculate_delivery_days(fecha_entrega, fecha_hora_correo)
                    dias_entrega = diff_dias_entrega.days

            # Obtenemos el seguimiento
            # seguimiento = self.querys.search_seguimiento(num_cot) # Seguimientos anteriores

            seguimiento = self.querys.buscar_seguimiento_historial(num_cot)

            # Armamos el JSON de respuesta
            response = {
                "cotizacion": datos,
                "informacion_extra": {
                    "dias_oportunidad": dias_oportunidad,
                    "dias_entrega": dias_entrega,
                    "seguimiento": seguimiento,
                },
            }

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", response)

        except Exception as e:
            print(f"Error al obtener información de cotización: {e}")
            raise CustomException("Error al obtener información de cotización.")

    # Api que guarda la cotización.
    def guardar_cotizacion(self, data: dict):
        try:
            # Iniciamos un diccionario vacio que será donde se guardara la información.
            data_insert = dict()

            # Asignamos los formatos de fecha deseados
            normal_format = "%d-%m-%Y %H:%M:%S"
            output_format = "%Y-%m-%d %H:%M:%S"

            # Asignamos toda la información entrante a sus respectivas variables
            email_sender = data.get("email_sender", "")
            email_subject = data.get("email_subject", "")
            email_datetime = data.get("email_datetime", "")
            if email_datetime:
                email_datetime = self.tools.format_date(email_datetime, normal_format, output_format)
                email_datetime = datetime.strptime(email_datetime, '%Y-%m-%d %H:%M:%S')
            nit = data.get("nit", "")
            nombre = data.get("nombre", "")
            coordinador = data.get("coordinador", "")
            ejecutivo = data.get("ejecutivo", "")
            tipo_cliente = data.get("tipo_cliente", "")
            zona = data.get("zona", "")
            fecha_vencimiento = data.get("fecha_vencimiento", None)
            if fecha_vencimiento:
                fecha_vencimiento = self.tools.format_date(fecha_vencimiento, normal_format, output_format)
                fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d %H:%M:%S')
            nueva_fecha_vencimiento = data.get("nueva_fecha_vencimiento", None)
            items_a_cotizar = data.get("items_a_cotizar", "")
            numero_cotizacion = data.get("numero_cotizacion", "")
            cotizacion_concepto = data.get("cotizacion_concepto", "")
            estado = data.get("estado", "")
            fecha_entrega = data.get("fecha_entrega", None)
            if fecha_entrega:
                fecha_entrega = self.tools.format_date(fecha_entrega, '%d-%m-%Y', '%Y-%m-%d')
                fecha_entrega = datetime.strptime(fecha_entrega, '%Y-%m-%d')
            usuario_creador_cotizacion = data.get("usuario_creador_cotizacion", "")
            pesos_cotizados = data.get("pesos_cotizados", None)
            if pesos_cotizados:
                pesos_cotizados = self.tools.format_money(pesos_cotizados)
            items_cotizados = data.get("items_cotizados", "")
            oportunidad_entrega = data.get("oportunidad_entrega", 0)
            dias_entrega = data.get("dias_entrega", 0)
            motivo_no_cotizacion = data.get("motivo_no_cotizacion", "")
            desvio_oportunidad = data.get("desvio_oportunidad", "")
            item_revisado_cumple = data.get("item_revisado_cumple", 0)
            item_revisado_muestra = data.get("item_revisado_muestra", 0)
            porcentaje_muestra = data.get("porcentaje_muestra", 0)
            desvio_calidad = data.get("desvio_calidad", "")
            autorizacion_desvio_oportunidad = data.get("autorizacion_desvio_oportunidad", None)
            autorizacion_desvio_calidad = data.get("autorizacion_desvio_calidad", None)

            # Validamos que no venga ni el correo, ni asunto ni fecha y hora vacias.
            if not email_sender or not email_subject or not email_datetime:
                raise CustomException("Error al guardar los datos en la base de datos.")
            
            # Consultamos si existe cotización.
            cotizacion = self.querys.buscar_cotizacion(
                email_sender,
                email_subject,
                email_datetime
            )

            # Armamos el JSON de guardado
            data_insert = {
                "email_sender": email_sender,
                "email_subject": email_subject,
                "email_datetime": email_datetime,
                "nit": nit if nit else '',
                "nombre": nombre if nombre else '',
                "coordinador": coordinador if coordinador else '',
                "ejecutivo": ejecutivo if ejecutivo else '',
                "tipo_cliente": tipo_cliente if tipo_cliente else '',
                "zona": zona if zona else '',
                "fecha_vencimiento": fecha_vencimiento if fecha_vencimiento else None,
                "items_a_cotizar": items_a_cotizar if items_a_cotizar else '',
                "numero_cotizacion": numero_cotizacion if numero_cotizacion else '',
                "cotizacion_concepto": cotizacion_concepto if cotizacion_concepto else '',
                "estado": estado,
                "fecha_entrega": fecha_entrega if fecha_entrega else None,
                "usuario_creador_cotizacion": usuario_creador_cotizacion if usuario_creador_cotizacion else '',
                "pesos_cotizados": pesos_cotizados if pesos_cotizados else None,
                "items_cotizados": items_cotizados if items_cotizados else '',
                "oportunidad_entrega": oportunidad_entrega if oportunidad_entrega else 0,
                "dias_entrega": dias_entrega if dias_entrega else 0,
                "nueva_fecha_vencimiento": nueva_fecha_vencimiento if nueva_fecha_vencimiento else None,
                "motivo_no_cotizacion": motivo_no_cotizacion.strip() if motivo_no_cotizacion else '',
                "desvio_oportunidad": desvio_oportunidad.strip() if desvio_oportunidad else '',
                "item_revisado_cumple": item_revisado_cumple,
                "item_revisado_muestra": item_revisado_muestra,
                "porcentaje_muestra": porcentaje_muestra,
                "desvio_calidad": desvio_calidad.strip() if desvio_calidad else '',
                "autorizacion_desvio_oportunidad": autorizacion_desvio_oportunidad if autorizacion_desvio_oportunidad else None,
                "autorizacion_desvio_calidad": autorizacion_desvio_calidad if autorizacion_desvio_calidad else None
            }

            # Validamos si existe, si no existe guardamos.
            if cotizacion:
                msg = "Ya existe un registro con esta información. ¿Desea guardar de todos modos?"
                return self.tools.output(210, msg)
            else:
                self.querys.insert_datos_coti(data_insert)

                return self.tools.output(200, "Datos guardados exitosamente en la base de datos.")

        except Exception as e:
            tb = traceback.format_exc()  # Captura el traceback completo como string
            print(f"Error al guardar la cotización: {e}\nTraceback: {tb}")
            # También puedes devolver el traceback si estás en modo debug
            raise CustomException(f"Error al guardar los datos en la base de datos")

    # Api que actualiza los datos de la cotización.
    def actualizar_cotizacion(self, data: dict):

        # Iniciamos un diccionario vacio que será donde se guardara la información.
        data_update = dict()
        data_valores_filtro = dict()

        # Asignamos los formatos de fecha deseados
        normal_format = "%d-%m-%Y %H:%M:%S"
        output_format = "%Y-%m-%d %H:%M:%S"

        # Asignamos toda la información entrante a sus respectivas variables
        email_sender = data.get("email_sender", "")
        email_subject = data.get("email_subject", "")
        email_datetime = data.get("email_datetime", "")
        if email_datetime:
            email_datetime = self.tools.format_date(email_datetime, normal_format, output_format)
            email_datetime = datetime.strptime(email_datetime, '%Y-%m-%d %H:%M:%S')
        nit = data.get("nit", "")
        nombre = data.get("nombre", "")
        coordinador = data.get("coordinador", "")
        ejecutivo = data.get("ejecutivo", "")
        tipo_cliente = data.get("tipo_cliente", "")
        zona = data.get("zona", "")
        fecha_vencimiento = data.get("fecha_vencimiento", None)
        if fecha_vencimiento:
            fecha_vencimiento = self.tools.format_date(fecha_vencimiento, normal_format, output_format)
            fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d %H:%M:%S')
        nueva_fecha_vencimiento = data.get("nueva_fecha_vencimiento", None)
        items_a_cotizar = data.get("items_a_cotizar", "")
        numero_cotizacion = data.get("numero_cotizacion", "")
        cotizacion_concepto = data.get("cotizacion_concepto", "")
        estado = data.get("estado", "")
        fecha_entrega = data.get("fecha_entrega", None)
        if fecha_entrega:
            fecha_entrega = self.tools.format_date(fecha_entrega, '%d-%m-%Y', '%Y-%m-%d')
            fecha_entrega = datetime.strptime(fecha_entrega, '%Y-%m-%d')
        usuario_creador_cotizacion = data.get("usuario_creador_cotizacion", "")
        pesos_cotizados = data.get("pesos_cotizados", None)
        if pesos_cotizados:
            pesos_cotizados = self.tools.format_money(pesos_cotizados)
        items_cotizados = data.get("items_cotizados", "")
        oportunidad_entrega = data.get("oportunidad_entrega", 0)
        dias_entrega = data.get("dias_entrega", 0)
        motivo_no_cotizacion = data.get("motivo_no_cotizacion", "")
        desvio_oportunidad = data.get("desvio_oportunidad", "")
        item_revisado_cumple = data.get("item_revisado_cumple", 0)
        item_revisado_muestra = data.get("item_revisado_muestra", 0)
        porcentaje_muestra = data.get("porcentaje_muestra", 0)
        desvio_calidad = data.get("desvio_calidad", "")
        autorizacion_desvio_oportunidad = data.get("autorizacion_desvio_oportunidad", None)
        autorizacion_desvio_calidad = data.get("autorizacion_desvio_calidad", None)

        # Validamos que no venga ni el correo, ni asunto ni fecha y hora vacias.
        if not email_sender or not email_subject or not email_datetime:
            raise CustomException("Error al guardar los datos en la base de datos.")

        # Armamos el JSON de guardado
        data_update = {
            "nit": nit if nit else '',
            "nombre": nombre if nombre else '',
            "coordinador": coordinador if coordinador else '',
            "ejecutivo": ejecutivo if ejecutivo else '',
            "tipo_cliente": tipo_cliente if tipo_cliente else '',
            "zona": zona if zona else '',
            "items_a_cotizar": items_a_cotizar if items_a_cotizar else '',
            "numero_cotizacion": numero_cotizacion if numero_cotizacion else '',
            "cotizacion_concepto": cotizacion_concepto if cotizacion_concepto else '',
            "estado": estado if estado else '',
            "fecha_entrega": fecha_entrega if fecha_entrega else None,
            "usuario_creador_cotizacion": usuario_creador_cotizacion if usuario_creador_cotizacion else '',
            "pesos_cotizados": pesos_cotizados if pesos_cotizados else None,
            "items_cotizados": items_cotizados if items_cotizados else '',
            "oportunidad_entrega": oportunidad_entrega if oportunidad_entrega else 0,
            "dias_entrega": dias_entrega if dias_entrega else 0,
            "nueva_fecha_vencimiento": nueva_fecha_vencimiento if nueva_fecha_vencimiento else None,
            "motivo_no_cotizacion": motivo_no_cotizacion.strip() if motivo_no_cotizacion else '',
            "desvio_oportunidad": desvio_oportunidad.strip() if desvio_oportunidad else '',
            "item_revisado_cumple": item_revisado_cumple,
            "item_revisado_muestra": item_revisado_muestra,
            "porcentaje_muestra": porcentaje_muestra,
            "desvio_calidad": desvio_calidad.strip() if desvio_calidad else '',
            "autorizacion_desvio_oportunidad": autorizacion_desvio_oportunidad if autorizacion_desvio_oportunidad else None,
            "autorizacion_desvio_calidad": autorizacion_desvio_calidad if autorizacion_desvio_calidad else None
        }

        data_valores_filtro = {
            "email_sender": email_sender,
            "email_subject": email_subject,
            "email_datetime": email_datetime,
            "fecha_vencimiento": fecha_vencimiento
        }

        self.querys.update_datos_coti(data_update, data_valores_filtro)
        
        flag_mod = False
        if estado == 'COT. ADJUDICACION':
            segui_coti_id = None

            # Si el estado es COT. ADJUDICACION, buscamos la cotización
            segui_coti_data = self.querys.buscar_cotizacion(
                email_sender,
                email_subject, 
                email_datetime
            )
            if segui_coti_data:
                segui_coti_id = segui_coti_data.id
                data_segui = self.querys.check_seguimiento_exists_2(
                    segui_coti_id,
                    numero_cotizacion
                )
                flag_mod = data_segui
                
        return self.tools.output(200, "Registro actualizado exitosamente.", flag_mod)

    # Api que carga los datos de la cotización.
    def cargar_datos_cotizacion(self, data: dict):

        # Iniciamos diccionario vacío,
        response = dict()

        # Asignamos los formatos de fecha deseados
        normal_format = "%d-%m-%Y %H:%M:%S"
        output_format = "%Y-%m-%d %H:%M:%S"

        # Asignamos toda la información entrante a sus respectivas variables
        email_sender = data.get("email_sender", "")
        email_subject = data.get("email_subject", "")
        email_datetime = data.get("email_datetime", "")
        if email_datetime:
            email_datetime = self.tools.format_date(email_datetime, normal_format, output_format)
            email_datetime = datetime.strptime(email_datetime, '%Y-%m-%d %H:%M:%S')

        # Validamos que no venga ni el correo, ni asunto ni fecha y hora vacias.
        if not email_sender or not email_subject or not email_datetime:
            raise CustomException("Seleccione un correo para comprobar su estado.")
        
        # Consultamos si existe cotización.
        cotizacion = self.querys.buscar_cotizacion(
            email_sender,
            email_subject,
            email_datetime
        )

        # Validamos si no existe la cotización.
        if not cotizacion:
            msg = "No se encontró un registro de seguimiento para el correo seleccionado."
            raise CustomException(msg)
        
        response = {
            "nit": cotizacion.nit,
            "nombre": cotizacion.nombre,
            "coordinador": cotizacion.coordinador,
            "ejecutivo": cotizacion.ejecutivo,
            "tipo_cliente": cotizacion.tipo_cliente,
            "zona": cotizacion.zona,
            "estado": cotizacion.estado,
            "fecha_vencimiento": datetime.strptime(str(cotizacion.fecha_vencimiento), "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M:%S") if cotizacion.fecha_vencimiento else '',
            "items_a_cotizar": cotizacion.items_a_cotizar,
            "numero_cotizacion": cotizacion.numero_cotizacion,
            "nueva_fecha_vencimiento": datetime.strptime(str(cotizacion.nueva_fecha_vencimiento), "%Y-%m-%d").strftime("%Y-%m-%d") if cotizacion.nueva_fecha_vencimiento else '',
            "motivo_no_cotizacion": cotizacion.motivo_no_cotizacion,
            "desvio_oportunidad": cotizacion.desvio_oportunidad,
            "item_revisado_cumple": cotizacion.item_revisado_cumple,
            "item_revisado_muestra": cotizacion.item_revisado_muestra,
            "porcentaje_muestra": cotizacion.porcentaje_muestra,
            "desvio_calidad": cotizacion.desvio_calidad,
            "autorizacion_desvio_oportunidad": cotizacion.autorizacion_desvio_oportunidad,
            "autorizacion_desvio_calidad": cotizacion.autorizacion_desvio_calidad
        }

        # Retornamos la respuesta
        return self.tools.output(200, "Datos cargados correctamente desde el seguimiento.", response)

    # Api que realiza la consulta del tercero a la base de datos.
    def get_terceros(self, data: dict):

        # Asignamos nuestros datos de entrada a sus respectivas variables
        valor = data["valor"]

        try:
            # Acá usamos la query para traer la información
            datos = self.querys.get_terceros(valor)

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", datos)

        except Exception as e:
            print(f"Error al obtener información de tercero: {e}")
            raise CustomException("Error al obtener información de tercero.")

    # Endpoint principal
    def calcular_dia_habil(self, data: dict):
        try:
            fecha_dt = datetime.strptime(data["fecha"], "%Y-%m-%d").date()
            feriados = self.obtener_feriados_colombia(fecha_dt.year)
            siguiente_habil = self.siguiente_dia_habil(fecha_dt, feriados)
            response = {
                "fecha_inicial": fecha_dt.isoformat(),
                "siguiente_dia_habil": siguiente_habil.isoformat()
            }
            return self.tools.output(200, "Operación exitosa.", response)
        except ValueError:
            raise CustomException("Formato de fecha inválido. Usa YYYY-MM-DD")

    # Obtener días festivos desde la API pública
    def obtener_feriados_colombia(self, anio: int):
        url = f"https://date.nager.at/api/v3/PublicHolidays/{anio}/CO"
        response = requests.get(url)
        if response.status_code == 200:
            feriados = [datetime.strptime(d['date'], "%Y-%m-%d").date() for d in response.json()]
            return feriados
        return []

    # Calcular siguiente día hábil
    def siguiente_dia_habil(self, fecha_inicial: datetime.date, feriados: list[datetime.date]) -> datetime.date:
        siguiente = fecha_inicial + timedelta(days=1)
        while siguiente.weekday() >= 5 or siguiente in feriados:
            siguiente += timedelta(days=1)
        return siguiente

    # Obtener contactos por nit
    def obtener_contactos(self, data: dict):
        """ Api que realiza la consulta de contactos a la base de datos. """

        # Asignamos nuestros datos de entrada a sus respectivas variables
        nit = data["nit"]

        try:
            # Acá usamos la query para traer la información
            contactos = self.querys.get_contactos_cotizacion(nit)

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", contactos)

        except Exception as e:
            print(f"Error al obtener información de contactos: {e}")
            raise CustomException("Error al obtener información de contactos.")

    # Api que guarda el seguimiento de la cotización desde la vista principal.
    def guardar_seguimiento_desde_principal(self, data: dict):
        
        try:
            # Asignamos los formatos de fecha deseados
            normal_format = "%d-%m-%Y %H:%M:%S"
            output_format = "%Y-%m-%d %H:%M:%S"

            # Asignamos toda la información entrante a sus respectivas variables
            email_sender = data.get("email_sender", "")
            email_subject = data.get("email_subject", "")
            email_datetime = data.get("email_datetime", "")
            if email_datetime:
                email_datetime = self.tools.format_date(email_datetime, normal_format, output_format)
                email_datetime = datetime.strptime(email_datetime, '%Y-%m-%d %H:%M:%S')
            numero_cotizacion = data.get("numero_cotizacion", "")
            usuario_creador_cotizacion = data.get("usuario_creador_cotizacion", "")
            fecha_programacion = data.get("fecha_programacion", None)
            hora_programacion = data.get("hora_programacion", None)
            contacto = data.get("contacto", None)
            fecha_programacion_final = datetime.strptime(
                f"{fecha_programacion} {hora_programacion}:00", '%Y-%m-%d %H:%M:%S'
                ) if fecha_programacion and hora_programacion else None
                
            segui_coti_data = self.querys.buscar_cotizacion(
                email_sender,
                email_subject, 
                email_datetime
            )
            if segui_coti_data:
                segui_coti_id = segui_coti_data.id
                data_guardar = {
                    "seguimiento_coti_id": segui_coti_id,
                    "cotizacion": numero_cotizacion,
                    "fecha_programacion": fecha_programacion_final,
                    "usuario": usuario_creador_cotizacion,
                    "contacto": contacto,
                    "flag": True
                }

                # Guardamos el seguimiento de la cotización
                segui_progra_id = self.querys.guardar_seguimiento(data_guardar)
                
                # Guardamos la historia del seguimiento de la cotización
                self.querys.guardar_historia_seguimiento(data_guardar, segui_progra_id)

            # Retornamos la información.
            return self.tools.output(200, "Seguimiento guardado exitosamente.")

        except Exception as e:
            print(f"Error al guardar el seguimiento: {e}")
            raise CustomException("Error al guardar el seguimiento.")
