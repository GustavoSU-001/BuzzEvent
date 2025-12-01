import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from typing import List, Dict, Optional, Any, Tuple
from google.cloud.firestore import Query, DocumentReference, DELETE_FIELD  # Importamos Query para tipado

# Asumo que Ubicacion.py y LocationService están disponibles en tu entorno
from Modulos.BaseDatos.Ubicacion import LocationService
from datetime import datetime
from dateutil.relativedelta import relativedelta
from geopy.geocoders import Nominatim
import uuid
import random

class Lectura_Eventos_DB:
    """
    Clase de servicio dedicada a la lectura de datos de Firestore
    para el proyecto BuzzEvent.
    """

    def __init__(self):
        self.obtencion_coordenadas()
        
        try:
            # Ruta de credenciales ajustada al formato asumido por tu código
            cred = credentials.Certificate("Modulos\\BaseDatos\\eva3-72fb2-firebase-adminsdk-hbxid-828018cca2.json")
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Conexión a Firebase (EVA3) establecida.")
            
            hoy=datetime.now()
            mes=hoy.month
            anio=hoy.year
            self.fecha=f'01-{mes}-{anio-1}'

        except Exception as e:
            self.db = None
            print(f"❌ ERROR de Conexión: No se pudo inicializar Firebase. {e}")

    def _check_db(self) -> bool:
        """Verifica si el cliente de DB está disponible antes de una consulta."""
        if not self.db:
            print("⛔ Operación fallida: El cliente de Firestore no está disponible.")
            return False
        return True
    
    
    def obtencion_coordenadas(self):
        coor = LocationService()
        self.coor_denadas = coor.obtener_mi_ubicacion()
        self.filtrar_coordenadas()
        
    
    def filtrar_coordenadas(self, latitud=None, longitud=None):
        if latitud and longitud:
            self.latitud = latitud
            self.longitud = longitud
        else: 
            self.latitud = self.coor_denadas['latitud']
            self.longitud = self.coor_denadas['longitud']
            
        if self.latitud and self.longitud:
            codigo_unico=uuid.uuid4().hex
            geolocator = Nominatim(user_agent=str(codigo_unico))
            location = geolocator.reverse((self.latitud, self.longitud), language='es')
            if location and 'address' in location.raw:
                direccion = location.raw['address']
                self.sector=f'{direccion.get("country", "Unknown")}_{direccion.get("state", "Unknown")}_{direccion.get("county", "Unknown")}_{direccion.get("city","Unknown")}'
            else:
                self.sector = 'Unknown'
        
        self.sector='Chile_Biobío_Biobío_Los Ángeles'

    
    def obtener_eventos_por_fecha(self, organizador=None, fecha_inicio=None, fecha_fin=None, etiquetas=None):
        if not self._check_db(): return {}
        
        # Debug: Print filter parameters
        print(f"DEBUG: Filtros aplicados - Organizador: {organizador}, Fecha Inicio: {fecha_inicio}, Fecha Fin: {fecha_fin}, Etiquetas: {etiquetas}")
        
        try:
            resultados = {}
            
            # 1. Obtener referencia al documento del sector
            doc_sector = self.db.collection("Sector").document(self.sector)
            
            # 2. Listar todas las colecciones (meses) dentro del sector
            colecciones_meses = list(doc_sector.collections())
            print(f"DEBUG: Colecciones encontradas en sector {self.sector}: {[c.id for c in colecciones_meses]}")
            
            # 3. Iterar sobre cada colección (mes)
            print(f"DEBUG: Buscando colecciones en sector: {self.sector}")
            for col in colecciones_meses:
                fecha_mes = col.id 
                print(f"DEBUG: Encontrada colección: {fecha_mes}")
                
                # Convertir fecha_mes a objeto datetime
                try:
                    fecha_mes_dt = datetime.strptime(fecha_mes, "%d-%m-%Y")
                except ValueError:
                    print(f"DEBUG: Saltando colección {fecha_mes} (formato inválido)")
                    continue 

                # Filtro optimizado de meses
                if fecha_inicio:
                    # Debug logic for start date
                    skip = False
                    if fecha_mes_dt.year < fecha_inicio.year:
                        skip = True
                    elif fecha_mes_dt.year == fecha_inicio.year and fecha_mes_dt.month < fecha_inicio.month:
                        skip = True
                    
                    if skip:
                        print(f"DEBUG: Saltando colección {fecha_mes} por ser anterior a fecha inicio {fecha_inicio.strftime('%d-%m-%Y')}")
                        continue  # Actually skip this collection 
                
                if fecha_fin:
                    if fecha_mes_dt.year > fecha_fin.year or (fecha_mes_dt.year == fecha_fin.year and fecha_mes_dt.month > fecha_fin.month):
                        print(f"DEBUG: Saltando colección {fecha_mes} por ser posterior a fecha fin {fecha_fin.strftime('%d-%m-%Y')}")
                        continue

                # 4. Obtener el documento "Eventos" de ese mes
                doc_eventos = col.document("Eventos").get()
                
                if doc_eventos.exists:
                    data = doc_eventos.to_dict()
                    print(f"DEBUG: Documento Eventos encontrado en {fecha_mes} con {len(data) if data else 0} eventos")
                    
                    # 5. Iterar sobre los eventos del mes
                    for id_evento, evento in data.items():
                        if not isinstance(evento, dict): continue
                        
                        # A. Filtro OBLIGATORIO por Organizador
                        # print(f"DEBUG: Revisando evento {id_evento}. Org: {evento.get('Organizador')} vs Buscado: {organizador}")
                        if organizador and evento.get('Organizador') != organizador:
                            continue
                        
                        # B. Filtro por Etiquetas (Tags)
                        if etiquetas:
                            evento_etiquetas = evento.get('Etiquetas', [])
                            if isinstance(evento_etiquetas, str):
                                evento_etiquetas = [evento_etiquetas]
                            
                            evento_etiquetas_lower = [t.lower().strip() for t in evento_etiquetas]
                            filtros_lower = [t.lower().strip() for t in etiquetas]
                            
                            if not any(tag in evento_etiquetas_lower for tag in filtros_lower):
                                continue

                        # Obtener fechas del evento
                        try:
                            inicio_val = evento['Fechas']['Fecha_Inicio']
                            termino_val = evento['Fechas']['Fecha_Termino']
                            
                            # Helper function to convert to datetime
                            def to_datetime(val):
                                if hasattr(val, 'date'):  # Firestore Timestamp or datetime object
                                    return val
                                elif isinstance(val, str):
                                    # Handle string formats
                                    if " " in val:
                                        val = val.split(" ")[0]
                                    
                                    if "-" in val:
                                        if val.index("-") == 4:  # YYYY-MM-DD
                                            return datetime.strptime(val, "%Y-%m-%d")
                                        else:  # DD-MM-YYYY
                                            return datetime.strptime(val, "%d-%m-%Y")
                                return None

                            inicio_dt = to_datetime(inicio_val)
                            termino_dt = to_datetime(termino_val)
                            
                            if not inicio_dt or not termino_dt:
                                print(f"DEBUG: Fechas inválidas para evento {id_evento}")
                                continue
                                
                            # Make naive for comparison (remove timezone info if present)
                            if hasattr(inicio_dt, 'tzinfo') and inicio_dt.tzinfo:
                                inicio_dt = inicio_dt.replace(tzinfo=None)
                            if hasattr(termino_dt, 'tzinfo') and termino_dt.tzinfo:
                                termino_dt = termino_dt.replace(tzinfo=None)
                            
                            # For debug logging
                            inicio_str = inicio_dt.strftime("%d-%m-%Y")
                            
                        except (KeyError, ValueError, TypeError) as e:
                            print(f"DEBUG: Error procesando fechas evento {id_evento}: {e}")
                            continue
                        
                        # C. Filtro por Fecha Inicio
                        if fecha_inicio:
                            if termino_dt < fecha_inicio:
                                print(f"DEBUG: Evento {id_evento} descartado. Termina {termino_dt} < Inicio {fecha_inicio}")
                                continue
                                
                        # D. Filtro por Fecha Fin
                        if fecha_fin:
                            if inicio_dt > fecha_fin:
                                print(f"DEBUG: Evento {id_evento} descartado. Inicia {inicio_dt} > Fin {fecha_fin}")
                                continue
                        
                        # Si pasa todos los filtros, agregar a resultados
                        print(f"DEBUG: Evento {id_evento} AGREGADO (Fecha: {inicio_str})")
                        resultados[id_evento] = evento

            print(f"DEBUG: Total eventos encontrados: {len(resultados)}")
            return resultados
        except Exception as e:
            print(f"Error en obtener_eventos_por_fecha: {e}")
            return {}
    
    def obtener_informacion(self, organizador=None, fecha_inicio=None, fecha_fin=None, etiquetas=None):
        if not self._check_db(): return []
        
        # Usar la nueva lógica de filtrado centralizada
        eventos = self.obtener_eventos_por_fecha(organizador, fecha_inicio, fecha_fin, etiquetas)
        
        eventos_filtrados3={}
        
        # Procesar los eventos obtenidos para el formato de salida
        for l, e in eventos.items():
            cantidad_v = len(e.get('Asistencia', []))
            asistencia = e.get('Asistencia', [])
            
            if cantidad_v > 0:
                cal = [ev.get('Calificacion', 0) for ev in asistencia]
                calificacion_t = round((sum(cal)/cantidad_v), 2)
            else:
                calificacion_t = 0.0
                
            archivos = e.get('Archivos', [])
            imagenes = [i['Direccion'] for i in archivos if i.get('Tipo') == 'Imagen']
            
            # Manejo seguro de claves anidadas
            ubicacion = e.get('Ubicacion', {}).get('Direccion', 'Sin dirección')
            fechas = e.get('Fechas', {})
            
            bloque = {
                'Titulo': e.get('Titulo', 'Sin Título'),
                'Descripcion': e.get('Descripcion', ''),
                'Calificacion': calificacion_t,
                'Imagenes': imagenes,
                'Ubicacion': ubicacion,
                'Etiquetas': e.get('Etiquetas', []),
                'Estado': e.get('Estado', 'Desconocido'),
                'Fecha_Inicio': fechas.get('Fecha_Inicio', ''),
                'Fecha_Termino': fechas.get('Fecha_Termino', '')
            }
            eventos_filtrados3[l]=bloque
                     
        return eventos_filtrados3
                

class Escritura_Eventos_DB:
    def __init__(self):
        self.obtencion_coordenadas()
        
        try:
            # Ruta de credenciales ajustada al formato asumido por tu código
            cred = credentials.Certificate("Modulos\\BaseDatos\\eva3-72fb2-firebase-adminsdk-hbxid-828018cca2.json")
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Conexión a Firebase (EVA3) establecida.")
            
            hoy=datetime.now()
            mes=hoy.month
            anio=hoy.year
            self.fecha=f'01-{mes}-{anio-1}'

        except Exception as e:
            self.db = None
            print(f"❌ ERROR de Conexión: No se pudo inicializar Firebase. {e}")

    def _check_db(self) -> bool:
        """Verifica si el cliente de DB está disponible antes de una consulta."""
        if not self.db:
            print("⛔ Operación fallida: El cliente de Firestore no está disponible.")
            return False
        return True
    
    
    def obtencion_coordenadas(self):
        coor = LocationService()
        self.coor_denadas = coor.obtener_mi_ubicacion()
        self.filtrar_coordenadas()
        
    
    def filtrar_coordenadas(self, latitud=None, longitud=None):
        if latitud and longitud:
            self.latitud = latitud
            self.longitud = longitud
        else: 
            self.latitud = self.coor_denadas['latitud']
            self.longitud = self.coor_denadas['longitud']
            
        if self.latitud and self.longitud:
            codigo_unico=uuid.uuid4().hex
            geolocator = Nominatim(user_agent=str(codigo_unico))
            location = geolocator.reverse((self.latitud, self.longitud), language='es')
            if location and 'address' in location.raw:
                direccion = location.raw['address']
                self.sector=f'{direccion.get("country", "Unknown")}_{direccion.get("state", "Unknown")}_{direccion.get("county", "Unknown")}_{direccion.get("city","Unknown")}'
            else:
                self.sector = 'Unknown'
        
        self.sector='Chile_Biobío_Biobío_Los Ángeles'


    def subir_evento(self, evento_data: Dict[str, Any]):
        if not self._check_db(): return

        # 1. Generar un ID ÚNICO para este evento.
        fecha = evento_data['Fechas']['Fecha_Termino']
        formato_fecha = '%d-%m-%Y %H:%M'

        # 1. Convertir la fecha final a objeto datetime
        #fecha_formateada1 = datetime.strptime(fecha, formato_fecha)
                
        año = fecha.year
        mes = fecha.month
                
        # 2. Crear un objeto datetime con el día forzado a 1
        fecha_primer_dia = datetime(año, mes, 1)

        # 3. CORRECCIÓN: Convertir el objeto datetime a STRING para usarlo como nombre de colección
        # Usamos strftime (datetime -> string) para obtener '01-mes-año'.
        timestamp_str = fecha_primer_dia.strftime('%d-%m-%Y') # Usar solo fecha, sin hora.
                
        # 4. Generar el ID único. Nota: No se puede interpolar un objeto datetime 
        # directamente en un f-string si quieres el formato. Usa strftime aquí también.
        # Usa solo caracteres seguros y un formato legible para la fecha
        fecha_id_str = fecha #_formateada1.strftime('%Y%m%d%H%M')
        event_id = f"Event-{random.randint(0, 1000)}-{fecha_id_str}"
        # ... (o simplemente deja fecha_formateada1, si quieres la representación por defecto)

        # 2. Construir la referencia al documento de 'Eventos'
        try:
            # Sector/{self.sector}/'01-mes-año'/Eventos
            doc_ref = (self.db.collection("Sector")
                      .document(self.sector)
                      .collection(f'{timestamp_str}') # <--- Ahora es un string válido
                      .document("Eventos"))
                    
            # 3. Preparar el payload: {event_id: evento_data}
            payload = {
                event_id: evento_data
            }

            # 4. Usar set con merge=True para añadir el nuevo campo sin sobrescribir.
            doc_ref.set(payload, merge=True)
            
            print(f"✅ Evento '{evento_data.get('Titulo', 'Sin Título')}' subido con éxito.")
            print(f"   ID asignado: {event_id}")
            return

        except Exception as e:
            print(f"❌ Error al intentar subir el evento: {e}")
            return
    
    def modificar_informacion(self, event_id: str, campo: str, nuevo_valor: Any = None, eliminar: bool = False):
        if not self._check_db(): return

        try:
            # 1. Referencia al documento 'Eventos' que contiene todos los eventos como campos
            doc_ref = (self.db.collection("Sector")
                    .document(self.sector)
                    .collection(self.fecha)
                    .document("Eventos"))
        except Exception as e:
            print(e)

            
        
    
    def subir_imagen(self):
        if not self._check_db(): return





        
#lect=Lectura_Eventos_DB()
#documento = lect.obtener_informacion('22.222.222-2')#lect.obtener_eventos_por_organizador('22.222.222-2')

#print(documento)



