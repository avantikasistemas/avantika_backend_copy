import requests
from Utils.tools import Tools, CustomException
from Utils.querys import Querys
from datetime import datetime

from Utils.constants import (
    MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT_ID, 
    MICROSOFT_API_SCOPE, MICROSOFT_URL, MICROSOFT_URL_GRAPH, PARENT_FOLDER,
    TARGET_FOLDER, EMAIL_USER
)

class Graph:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()
        self.querys = Querys(self.db)
        self.token = self._get_access_token()

    def get_emails(self, data: dict):
        """ Api interna donde realizaremos la lógica para extracción de los correos. """

        # Inicializamos 2 listas vacias
        emails = list()
        response = list()

        # Asignamos nuestros datos de entrada a sus respectivas variables
        start_date = data["start_date"]
        end_date = data["end_date"]
        
        # Asignamos los formatos de fecha deseados
        normal_format = "%d-%m-%Y"
        output_format = "%Y-%m-%d"

        # Formateamos las fechas a un formato valido si existen
        if start_date:
            start_date = self.tools.format_date(start_date, normal_format, output_format)
        if end_date:    
            end_date = self.tools.format_date(end_date, normal_format, output_format)

        try:
            # llamamos a la funcion extract emails para extraer los correos desde la api externa
            emails = self.extract_emails(start_date, end_date)

            # Ordenar correos de más reciente a más antiguo antes de añadirlos a la tabla
            emails.sort(key=lambda x: x['receivedDateTime'], reverse=True)
            print(f"Correos extraídos: {len(emails)}")

            # Filtramos los correos evitando enviar los de spam
            filtered_emails = [
                email for email in emails
                if not email['from']['emailAddress']['address'].lower().startswith(('postmaster', 'noreply'))
                and not email['subject'].startswith(('[!!Spam]', '[!!Massmail]'))
            ]

            # Ordenamos por fecha de la actual a la antigua
            filtered_emails.sort(key=lambda x: x['receivedDateTime'], reverse=True)

            # Recorremos los correos para realizar el formato de respuesta
            if emails: 
                for i, email in enumerate(emails):
                    # Asignamos los datos de correo a variables
                    sender = email['from']['emailAddress']['address']
                    subject = email['subject']
                    received_time_iso = email['receivedDateTime']
                    # Formateamos la fecha
                    received_time = self.tools.format_datetime(received_time_iso)

                    # Obtener el estado del seguimiento
                    seguimiento = self.querys.check_follow_up(sender, subject, received_time)

                    # Guardamos los datos en nuestra variable respuesta y la formateamos en json
                    response.append({
                        "id": i+1,
                        "remitente": sender,
                        "asunto": subject,
                        "fecha_hora": received_time,
                        "seguimiento": seguimiento,
                        "body": email.get('body', {}).get('content', ''),
                    })

            # Retornamos la información.
            return self.tools.output(200, "Datos encontrados.", response)

        except Exception as e:
            print(f"Error al extraer correos: {e}")
            raise CustomException("Error al extraer correos.")

    def extract_emails(self, start_date, end_date):

        """Recupera correos electrónicos de una carpeta específica, opcionalmente dentro de un rango de fechas."""
        folder_id = self.get_folder_id(PARENT_FOLDER, TARGET_FOLDER)
        if not folder_id:
            return []

        filter_query = ""
        if start_date and end_date:
            filter_query = f"&$filter=receivedDateTime ge {start_date}T00:00:00Z and receivedDateTime le {end_date}T23:59:59Z"

        url = f"{MICROSOFT_URL_GRAPH}{EMAIL_USER}/mailFolders/{folder_id}/messages?$top=100{filter_query}&$select=from,subject,receivedDateTime,bodyPreview,body"
        
        emails = []
        max_iterations = 100
        iteration = 0

        while url and iteration < max_iterations:
            print(f"Haciendo solicitud a: {url}")
            data = self._make_request(url)
            if not data:
                break
            
            new_emails = data.get('value', [])
            if not new_emails:
                print("No se recuperaron nuevos correos. Deteniendo.")
                break
            
            emails.extend(new_emails)
            url = data.get('@odata.nextLink')  # Paginación
            iteration += 1

        return emails

    def get_folder_id(self, parent_folder: str, target_folder: str):

        """Obtiene el ID de una carpeta específica dentro del correo del usuario."""
        url = f"{MICROSOFT_URL_GRAPH}{EMAIL_USER}/mailFolders/{parent_folder}/childFolders"
        data = self._make_request(url)
        if data:
            for folder in data.get('value', []):
                if folder['displayName'] == target_folder:
                    return folder['id']
        print(f"No se encontró la carpeta {target_folder}.")
        return None

    def _make_request(self, endpoint):
        """Realiza una petición GET a Microsoft Graph API."""
        if not self.token:
            print("No se pudo obtener el token de acceso.")
            return None

        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        print(f"Error en la solicitud: {response.status_code} - {response.text}")
        return None

    def _get_access_token(self):
        """Obtiene el token de acceso para autenticarse en Microsoft Graph API."""
        url = f"{MICROSOFT_URL}{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'client_id': MICROSOFT_CLIENT_ID,
            'scope': ' '.join(MICROSOFT_API_SCOPE),
            'client_secret': MICROSOFT_CLIENT_SECRET,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json().get('access_token')
        print(f"Error obteniendo el token: {response.status_code} - {response.text}")
        return None

    def actualizar_estado_seguimiento(self, data: dict):

        email_list = data["email_list"]
        new_email_list = list()

        # Asignamos los formatos de fecha deseados
        normal_format = "%d-%m-%Y %H:%M:%S"
        output_format = "%Y-%m-%d %H:%M:%S"

        # Validamos si hay correos
        if not email_list:
            raise CustomException("No hay una lista de correos a actualizar.")
        
        # Consultamos el seguimiento de cada uno de los correos
        for email in email_list:
            id = email["id"]
            remitente = email["remitente"]
            asunto = email["asunto"]
            fecha_hora = email["fecha_hora"]
            if fecha_hora:
                new_fecha_hora = self.tools.format_date(fecha_hora, normal_format, output_format)
                new_fecha_hora = datetime.strptime(new_fecha_hora, '%Y-%m-%d %H:%M:%S')
            seguimiento = self.querys.check_follow_up(
                remitente,
                asunto,
                new_fecha_hora,
            )
            body = email["body"]

            # Armamos una lista con los correos y sus seguimientos actualizados
            new_email_list.append({
                "id": id,
                "remitente": remitente,
                "asunto": asunto,
                "fecha_hora": fecha_hora,
                "seguimiento": seguimiento,
                "body": body
            })
        # Retornamos la lista
        return self.tools.output(200, "Nueva lista exitosa.", new_email_list)
