
from Utils.tools import Tools, CustomException
from sqlalchemy import func, and_, text
from Models.seguimiento_coti_model import SeguimientoCotiModel
from sqlalchemy.orm import Session
from datetime import datetime
import traceback

class Querys:

    def __init__(self, db):
        self.db = db
        self.tools = Tools()

    # Query para obtener el estado del seguimiento, si no lo tiene se agrega 'sin seguimiento'
    def check_follow_up(self, sender: str, subject: str, received_time: str):

        try:
            query = self.db.query(
                SeguimientoCotiModel
            ).filter(
                SeguimientoCotiModel.email_sender == sender,
                SeguimientoCotiModel.email_subject == subject,
                SeguimientoCotiModel.email_datetime == received_time
            ).first()                 

            # Devolvemos el estado si la consulta encuentra una fila
            if query:
                if query.estado == '' or not query.estado:
                    return "Sin seguimiento"
                else:
                    return query.estado
            else:
                return "Sin seguimiento"
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para obtener los datos del tercero por medio del nit
    def get_tercero_x_nit(self, nit: str):

        response = {
            "nit": "No encontrado",
            "nombres": "No encontrado",
            "coordinador": "No encontrado",
            "ejecutivo": "No encontrado",
            "tipo_cliente": "No encontrado",
            "zona": "No encontrado",
        }
        try:
            sql = """
                SELECT t.nit, t.nombres, tv.coordinador, tv.ejecutivo, dbo.terceros_16.descripcion AS 'tipo_cliente', dbo.terceros_2.descripcion AS 'zona'
                FROM   dbo.terceros AS t 
                INNER JOIN dbo.terceros_ventas AS tv ON t.concepto_2 = tv.concepto_2 
                INNER JOIN dbo.terceros_16 ON t.concepto_16 = dbo.terceros_16.concepto_16 
                INNER JOIN dbo.terceros_2 ON t.concepto_2 = dbo.terceros_2.concepto_2
                WHERE t.nit = :nit;
            """

            query = self.db.execute(text(sql), {"nit": nit}).fetchone()

            if query:
                response.update({
                    "nit": query.nit,
                    "nombres": query.nombres,
                    "coordinador": query.coordinador,
                    "ejecutivo": query.ejecutivo,
                    "tipo_cliente": query.tipo_cliente,
                    "zona": query.zona,
                })

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()
    
    # Query para obtener los tipos de estado para la cotizacion
    def get_tipos_estado(self):

        try:
            response = list()
            sql = """
                SELECT * FROM tipo_transacciones_concep2_ped WHERE sw = 2 ORDER BY concepto ASC;
            """

            query = self.db.execute(text(sql)).fetchall()
            if query:
                for key in query:
                    response.append(key[2])

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()
    
    # Query para obtener los datos de la cotizacion
    def consultar_cotizacion(self, num_cot):

        try:
            response = list()
            sql = """
                SELECT DISTINCT TOP (40000) 
                    t1.descripcion AS descripcion_concep1,
                    t2.descripcion AS descripcion_concep2,
                    dp.fecha_hora_entrega,
                    dp.usuario,
                    -- Cálculo del total ajustado
                    (SELECT SUM(cantidad * valor_unitario) 
                    FROM dbo.documentos_lin_ped dl
                    WHERE dl.numero = dp.numero AND dl.sw = dp.sw) AS Pesos_cotizados,
                    
                    -- Conteo de filas
                    (SELECT COUNT(*)
                    FROM dbo.documentos_lin_ped dl
                    WHERE dl.numero = dp.numero AND dl.sw = dp.sw) AS CantidadFilas
                FROM dbo.documentos_ped dp
                INNER JOIN dbo.tipo_transacciones_concep_ped t1 
                    ON dp.sw = t1.sw AND dp.concepto = t1.concepto
                INNER JOIN dbo.tipo_transacciones_concep2_ped t2 
                    ON dp.concepto2 = t2.concepto
                WHERE dp.numero = :numero AND dp.sw = 2;
            """

            query = self.db.execute(text(sql), {"numero": num_cot}).fetchall()
            if query:
                for i, key in enumerate(query):
                    fecha_hora_entrega = key.fecha_hora_entrega if key.fecha_hora_entrega else ""
                    fecha_hora_entrega_str = self.tools.format_date2(str(key.fecha_hora_entrega)) if key.fecha_hora_entrega else ""
                    pesos_cotizados = f"{float(key.Pesos_cotizados):,.2f}" if key.Pesos_cotizados else 0
                    response.append({
                        "id": i+1,
                        "descripcion_concep1": key.descripcion_concep1,
                        "descripcion_concep2": key.descripcion_concep2,
                        "fecha_hora_entrega": fecha_hora_entrega,
                        "fecha_hora_entrega_str": fecha_hora_entrega_str,
                        "usuario": key.usuario,
                        "pesos_cotizados": pesos_cotizados,
                        "cantidad_filas": key.CantidadFilas,
                    })

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para obtener la información del seguimiento.
    def search_seguimiento(self, num_cot):

        try:
            response = "No tiene seguimiento"
            result = ""
            sql = """
                SELECT des_usuario AS 'Usuario', Desc_actividad AS 'Actividad', Desc_resultado AS 'Resultado_Seguimiento', comentario AS 'Comentario',Fecha_creacion
                FROM Q_Seguimiento_Actividades_CRM
                WHERE documento = :documento;
            """
            query = self.db.execute(text(sql), {"documento": num_cot}).fetchall()

            if query:
                for key in query:
                    result += f"Usuario: {key.Usuario}\n"
                    result += f"Actividad: {key.Actividad}\n"
                    result += f"Resultado_Seguimiento: {key.Resultado_Seguimiento}\n"
                    result += f"Comentario: {key.Comentario}\n"
                    result += f"Fecha_creacion: {key.Fecha_creacion}\n"
                    result += "-" * 70 + "\n"

                response = result

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para buscar si la cotizacion existe
    def buscar_cotizacion(self, sender: str, subject: str, received_time: str):

        try:
            query = self.db.query(
                SeguimientoCotiModel
            ).filter(
                SeguimientoCotiModel.email_sender == sender,
                SeguimientoCotiModel.email_subject == subject,
                SeguimientoCotiModel.email_datetime == received_time
            ).first()                 

            # Devolvemos si hay registro
            return query
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para insertar datos de la cotizacion.
    def insert_datos_coti(self, data: dict):
        try:
            details = SeguimientoCotiModel(data)
            self.db.add(details)
            self.db.commit()
        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()
        return True

    # Query para actualizar los datos de la cotizacion.
    def update_datos_coti(self, data: dict, data_filtros: dict):
        try:
            rows_updated = self.db.query(
                SeguimientoCotiModel
            ).filter(
                SeguimientoCotiModel.email_sender == data_filtros["email_sender"],
                SeguimientoCotiModel.email_subject == data_filtros["email_subject"],
                SeguimientoCotiModel.email_datetime == data_filtros["email_datetime"]
            ).update(data)                     
            self.db.commit()
            if rows_updated == 0:
                print("No se encontró ningún registro para actualizar.")
                
        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

        return True

    # Query para obtener los datos del tercero por medio del nit
    def get_terceros(self, valor: str):

        response = list()
        try:
            sql = """
                SELECT t.nit, t.nombres, tv.coordinador, tv.ejecutivo, dbo.terceros_16.descripcion AS 'tipo_cliente', dbo.terceros_2.descripcion AS 'zona'
                FROM   dbo.terceros AS t 
                INNER JOIN dbo.terceros_ventas AS tv ON t.concepto_2 = tv.concepto_2 
                INNER JOIN dbo.terceros_16 ON t.concepto_16 = dbo.terceros_16.concepto_16 
                INNER JOIN dbo.terceros_2 ON t.concepto_2 = dbo.terceros_2.concepto_2
                WHERE (t.nit LIKE :valor OR t.nombres LIKE :valor)
            """

            query = self.db.execute(text(sql), {"valor": f"%{valor}%"}).fetchall()

            if query:
                for key in query:   
                    response.append({
                        "nit": key.nit,
                        "nombres": key.nombres,
                        "coordinador": key.coordinador,
                        "ejecutivo": key.ejecutivo,
                        "tipo_cliente": key.tipo_cliente,
                        "zona": key.zona,
                    })

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para revisar si la cotización existe en la base de datos.
    def check_if_cotizacion_exists(self, cotizacion: str):

        try:
            result = dict()
            sql = """
                SELECT DISTINCT TOP (40000) 
                    t1.descripcion AS descripcion_concep1,
                    t2.descripcion AS descripcion_concep2,
                    dp.fecha_hora_entrega,
                    dp.usuario,
                    -- Cálculo del total ajustado
                    (SELECT SUM(cantidad * valor_unitario) 
                    FROM dbo.documentos_lin_ped dl
                    WHERE dl.numero = dp.numero AND dl.sw = dp.sw) AS Pesos_cotizados,
                                    
                    -- Conteo de filas
                    (SELECT COUNT(*)
                    FROM dbo.documentos_lin_ped dl
                    WHERE dl.numero = dp.numero AND dl.sw = dp.sw) AS CantidadFilas,
                    dp.nit, t.nombres as nombre_tercero
                FROM dbo.documentos_ped dp
                INNER JOIN dbo.tipo_transacciones_concep_ped t1 
                    ON dp.sw = t1.sw AND dp.concepto = t1.concepto
                INNER JOIN dbo.tipo_transacciones_concep2_ped t2 
                    ON dp.concepto2 = t2.concepto
                INNER JOIN terceros t on t.nit = dp.nit
                WHERE dp.numero = :numero AND dp.sw = 2;
            """
            query = self.db.execute(text(sql), {"numero": cotizacion}).fetchone()
            
            if not query:
                raise CustomException("No se encontró la cotización.")
            
            result = {
                "descripcion_concep1": query.descripcion_concep1,
                "descripcion_concep2": query.descripcion_concep2,
                "fecha_hora_entrega": str(query.fecha_hora_entrega) if query.fecha_hora_entrega else "",
                "usuario": query.usuario,
                "Pesos_cotizados": f"{float(query.Pesos_cotizados):,.2f}" if query.Pesos_cotizados else 0,
                "nit": query.nit,
                "nombre_tercero": query.nombre_tercero,
            }
            
            return result

        except CustomException as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para guardar el seguimiento de la cotización.
    def guardar_seguimiento(self, data: dict, data_segui_coti_id: int = None):
        try:

            flag = data["flag"]
            if flag is False:
                sql = """
                    INSERT INTO dbo.seguimiento_programacion (seguimiento_coti_id, numero, fecha_programacion, usuario)
                    OUTPUT INSERTED.id
                    VALUES (:seguimiento_coti_id, :numero, :fecha_programacion, :usuario)
                """
                result = self.db.execute(text(sql), {
                    "seguimiento_coti_id": data_segui_coti_id,
                    "numero": data["cotizacion"],
                    "fecha_programacion": data["fecha_programacion"],
                    "usuario": data["usuario"]
                })
            else:
                sql = """
                    INSERT INTO dbo.seguimiento_programacion (seguimiento_coti_id, numero, fecha_programacion, usuario)
                    OUTPUT INSERTED.id
                    VALUES (:seguimiento_coti_id, :numero, :fecha_programacion, :usuario)
                """
                result = self.db.execute(text(sql), {
                    "seguimiento_coti_id": data["seguimiento_coti_id"],
                    "numero": data["cotizacion"],
                    "fecha_programacion": data["fecha_programacion"],
                    "usuario": data["usuario"]
                })
                
            inserted_id = result.scalar()  # Captura el ID insertado
            self.db.commit()
            return inserted_id

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para guardar la historia del seguimiento de la cotización.
    def guardar_historia_seguimiento(self, data, segui_progra_id):
        try:
            flag = data.get("flag", True)
            if flag is False:
                sql = """
                    INSERT INTO dbo.seguimiento_programacion_historia (seguimiento_programacion_id, numero, fecha_programacion, usuario, tipo_seguimiento, contacto)
                    VALUES (:seguimiento_programacion_id, :numero, :fecha_programacion, :usuario, :tipo_seguimiento, :contacto)
                """
                self.db.execute(text(sql), {
                    "seguimiento_programacion_id": segui_progra_id,
                    "numero": data["cotizacion"],
                    "fecha_programacion": data["fecha_programacion"],
                    "usuario": data["usuario"],
                    "tipo_seguimiento": data.get("tipo_seguimiento", 1),
                    "contacto": data.get("contacto", None)
                })
            else:
                sql = """
                    INSERT INTO dbo.seguimiento_programacion_historia (seguimiento_programacion_id, numero, fecha_programacion, usuario, tipo_seguimiento, contacto)
                    VALUES (:seguimiento_programacion_id, :numero, :fecha_programacion, :usuario, :tipo_seguimiento, :contacto)
                """
                self.db.execute(text(sql), {
                    "seguimiento_programacion_id": segui_progra_id,
                    "numero": data["cotizacion"],
                    "fecha_programacion": data["fecha_programacion"],
                    "usuario": data["usuario"],
                    "tipo_seguimiento": data.get("tipo_seguimiento", 1),
                    "contacto": data.get("contacto", None)
                })
            self.db.commit()
        except Exception as ex:
            print(f"{ex}")
            print(traceback.format_exc())  
            raise CustomException(str(ex))
        finally:
            self.db.close()
        return True

    # Query para obtener la historia del seguimiento de la cotización.
    def get_historia_seguimiento(self, cotizacion: str):
        try:
            response = list()
            sql = """
                SELECT sph.id, sph.numero, sph.fecha_programacion, sph.usuario, ts.nombre AS tipo_seguimiento, sph.contacto, sph.resultado_seguimiento
                FROM dbo.seguimiento_programacion_historia sph
                LEFT JOIN dbo.tipo_seguimientos ts ON ts.id = sph.tipo_seguimiento
                WHERE sph.numero = :numero AND sph.estado = 1;
            """
            query = self.db.execute(text(sql), {"numero": cotizacion}).fetchall()
            for index, row in enumerate(query):
                response.append({
                    "index": index + 1,
                    "id": row.id,
                    "numero": row.numero,
                    "fecha_programacion": str(row.fecha_programacion) if row.fecha_programacion else "",
                    "usuario": row.usuario,
                    "tipo_seguimiento": row.tipo_seguimiento,
                    "contacto": row.contacto,
                    "resultado_seguimiento": row.resultado_seguimiento
                })
            return response

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para obtener los tipos de seguimiento.
    def tipo_seguimientos(self):
        try:
            response = list()
            sql = """
                SELECT * FROM tipo_seguimientos WHERE estado = 1;
            """

            query = self.db.execute(text(sql)).fetchall()
            if query:
                for key in query:
                    response.append({
                        "id": key.id,
                        "nombre": key.nombre
                    })

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para obtener los contactos de la cotización.            
    def get_contactos_cotizacion(self, nit: int):
        try:
            response = list()
            sql = """
                SELECT * FROM CRM_contactos WHERE nit = :nit AND tel_celular IS NOT NULL;
            """
            query = self.db.execute(text(sql), {"nit": nit}).fetchall()
            for row in query:
                response.append({
                    "tel_celular": row.tel_celular,
                    "nombre": row.nombre.upper()
                })
            return response

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para obtener los tipos de resultado de llamada.
    def tipo_resultado_llamada(self):
        try:
            response = list()
            sql = """
                SELECT * FROM seguimiento_resultado_llamada WHERE estado = 1;
            """

            query = self.db.execute(text(sql)).fetchall()
            if query:
                for key in query:
                    response.append({
                        "id": key.id,
                        "nombre": key.nombre
                    })

            return response
                
        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para verificar si el seguimiento existe por ID y número.
    def check_seguimiento_id(self, data: dict):
        try:
            sql = """
                SELECT * FROM dbo.seguimiento_programacion_historia WHERE id = :id AND numero = :numero;
            """
            query = self.db.execute(text(sql), {"id": data["id"], "numero": data["numero"]}).first()
            if not query:
                raise CustomException("No se encontró el seguimiento con el ID y número proporcionados.")
            return True

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para actualizar el resultado de la llamada.
    def actualizar_resultado_llamada(self, data: dict):
        try:

            sql = """
                UPDATE dbo.seguimiento_programacion_historia 
                SET resultado_seguimiento = :resultado_llamada
                WHERE id = :id AND numero = :numero AND estado = 1;
            """
            self.db.execute(text(sql), {
                "resultado_llamada": data["resultado_llamada"],
                "id": data["id"],
                "numero": data["numero"]
            })
            self.db.commit()

            sql2 = """
                UPDATE dbo.seguimiento_programacion 
                SET resultado_seguimiento = :resultado_llamada
                WHERE numero = :numero AND estado = 1;
            """
            self.db.execute(text(sql2), {
                "resultado_llamada": data["resultado_llamada"],
                "numero": data["numero"]
            })
            self.db.commit()
            
            # Consulta del objeto actualizado desde la tabla principal
            sql_select = """
                SELECT * FROM dbo.seguimiento_programacion 
                WHERE numero = :numero AND estado = 1;
            """
            result = self.db.execute(text(sql_select), {"numero": data["numero"]}).fetchone()

            return result.resultado_seguimiento if result else None

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para verificar si el seguimiento de la cotización ya existe.
    def check_seguimiento_exists(self, cotizacion: str):
        try:
            sql = """
                SELECT * FROM dbo.seguimiento_programacion WHERE numero = :numero AND estado = 1;
            """
            query = self.db.execute(text(sql), {"numero": cotizacion}).first()
            if not query:
                return False
            return query

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para obtener los motivos de no adjudicación.
    def motivos_no_adjudicacion(self):
        try:
            response = list()
            sql = """
                SELECT * FROM dbo.seguimiento_programacion_motivo_no_adjudicacion WHERE estado = 1;
            """

            query = self.db.execute(text(sql)).fetchall()
            if query:
                for key in query:
                    response.append({
                        "id": key.id,
                        "nombre": key.nombre
                    })

            return response

        except Exception as ex:
            print(str(ex))
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para guardar la información de no adjudicación.
    def guardar_no_adjudicacion(self, data: dict):
        try:
            sql = """
                UPDATE dbo.seguimiento_programacion SET resultado_seguimiento = :resultado_seguimiento, motivo_no_adjudicacion_id = :motivo_no_adjudicacion_id, 
                razon_no_adjudicacion = :razon_no_adjudicacion, fecha_no_adjudicacion = :fecha_no_adjudicacion
                WHERE numero = :numero AND estado = 1;
            """
            self.db.execute(text(sql), {
                "resultado_seguimiento": data["resultado_llamada"],
                "motivo_no_adjudicacion_id": data["motivo_no_adjudicacion"],
                "razon_no_adjudicacion": data["razon_no_adjudicacion"],
                "fecha_no_adjudicacion": datetime.now(),
                "numero": data["cotizacion"]
            })
            self.db.commit()
            
            sql2 = """
                UPDATE dbo.seguimiento_programacion_historia 
                SET resultado_seguimiento = :resultado_seguimiento
                WHERE id = :id AND numero = :numero AND estado = 1;
            """
            self.db.execute(text(sql2), {
                "resultado_seguimiento": data["resultado_llamada"],
                "id": data["id"],
                "numero": data["numero"]
            })
            self.db.commit()
            
            # Consulta del objeto actualizado desde la tabla principal
            sql_select = """
                SELECT * FROM dbo.seguimiento_programacion 
                WHERE numero = :numero AND estado = 1;
            """
            result = self.db.execute(text(sql_select), {"numero": data["numero"]}).fetchone()

            return result.resultado_seguimiento if result else None

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para obtener el resultado del seguimiento de la cotización.
    def get_data_seguimiento(self, cotizacion: str):
        try:
            sql = """
                SELECT * FROM dbo.seguimiento_programacion WHERE numero = :numero AND estado = 1;
            """
            query = self.db.execute(text(sql), {"numero": cotizacion}).first()

            return None if not query else {
                "id": query.id,
                "numero": query.numero,
                "fecha_programacion": str(query.fecha_programacion) if query.fecha_programacion else "",
                "usuario": query.usuario,
                "resultado_seguimiento": query.resultado_seguimiento,
                "motivo_no_adjudicacion_id": query.motivo_no_adjudicacion_id,
                "razon_no_adjudicacion": query.razon_no_adjudicacion,
                "fecha_no_adjudicacion": str(query.fecha_no_adjudicacion) if query.fecha_no_adjudicacion else "",
                "razon_adjudicacion": query.razon_adjudicacion,
                "fecha_adjudicacion": str(query.fecha_adjudicacion) if query.fecha_adjudicacion else "",
                "comentario_en_estudio": query.comentario_en_estudio
            }

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para guardar el seguimiento en estudio.
    def guardar_en_estudio(self, data: dict):
        try:            
            sql = """
                UPDATE dbo.seguimiento_programacion SET resultado_seguimiento = :resultado_seguimiento, 
                comentario_en_estudio = :comentario_en_estudio
                WHERE numero = :numero AND estado = 1;
            """
            self.db.execute(text(sql), {
                "resultado_seguimiento": data["resultado_llamada"],
                "comentario_en_estudio": data["comentario_en_estudio"],
                "numero": data["cotizacion"]
            })
            self.db.commit()
            
            sql2 = """
                UPDATE dbo.seguimiento_programacion_historia 
                SET resultado_seguimiento = :resultado_seguimiento
                WHERE id = :id AND numero = :numero AND estado = 1;
            """
            self.db.execute(text(sql2), {
                "resultado_seguimiento": data["resultado_llamada"],
                "id": data["id"],
                "numero": data["numero"]
            })
            self.db.commit()
            
            # Consulta del objeto actualizado desde la tabla principal
            sql_select = """
                SELECT * FROM dbo.seguimiento_programacion 
                WHERE numero = :numero AND estado = 1;
            """
            result = self.db.execute(text(sql_select), {"numero": data["numero"]}).fetchone()

            return result.resultado_seguimiento if result else None

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para buscar el historial de seguimiento de la cotización.
    def buscar_seguimiento_historial(self, num_cot):
        try:        
            response = "No tiene seguimiento"
            result = ""
            sql = """
                select sph.fecha_programacion, sph.usuario, srl.nombre as resultado_seguimiento, ts.nombre as tipo_seguimiento, 
                sph.contacto, sph.created_at as fecha_creacion
                from seguimiento_programacion_historia sph
                inner join seguimiento_resultado_llamada srl on srl.id = sph.resultado_seguimiento  
                inner join tipo_seguimientos ts on ts.id = sph.tipo_seguimiento  
                where sph.estado = 1
                AND srl.estado = 1
                AND ts.estado = 1
                AND numero = :numero
            """
            query = self.db.execute(text(sql), {"numero": num_cot}).fetchall()

            if query:
                for key in query:
                    result += f"Usuario: {key.usuario}\n"
                    result += f"Fecha Programación: {key.fecha_programacion}\n"
                    result += f"Resultado Seguimiento: {key.resultado_seguimiento}\n"
                    result += f"Tipo Seguimiento: {key.tipo_seguimiento}\n"
                    result += f"Fecha creacion: {str(key.fecha_creacion)}\n"
                    result += "-" * 70 + "\n"

                response = result

            return response

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para verificar si el seguimiento de la cotización ya existe.
    def check_seguimiento_exists_2(self, segui_coti_id: int, cotizacion: str):
        try:
            sql = """
                SELECT * 
                FROM dbo.seguimiento_programacion 
                WHERE seguimiento_coti_id = :seguimiento_coti_id
                AND numero = :numero
                AND estado = 1;
            """
            query = self.db.execute(text(sql), {
                    "seguimiento_coti_id": segui_coti_id, 
                    "numero": cotizacion
                }).first()
            if not query:
                return False
            return True

        except Exception as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()

    # Query para verificar si existe un correo asociado a la cotización.
    def check_seguimiento_coti_correo_exists(self, num_cot):
        try:
            sql = """
                SELECT * 
                FROM dbo.seguimiento_coti 
                WHERE numero_cotizacion = :numero;
            """
            query = self.db.execute(text(sql), {"numero": num_cot}).fetchone()
            
            if not query:
                raise CustomException(
                    "Este número de cotización no tiene correo asociado."
                )
            return dict(query._mapping)

        except CustomException as ex:
            raise CustomException(str(ex))
        finally:
            self.db.close()
