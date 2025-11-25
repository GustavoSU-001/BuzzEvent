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

    
    def obtener_eventos_por_fecha(self, organizador=None, fecha_inicio=None, fecha_fin=None):
        if not self._check_db(): return {}
        try:
            resultados = {}
            
            quer = self.db.collection("Sector")
            quer2=quer.document(self.sector)
            dos = quer2.collections()
            data2 = [d.id for d in dos]
            for f in data2:
                if fecha_inicio:
                    if fecha_inicio > f:
                        continue
                if fecha_fin:
                    if decha_fin <f:
                        continue
                query = self.db.collection("Sector")
                query2=query.document(self.sector)
                query3=query2.collection(f)
                query4=query3.document("Eventos")
                
                docs = query4.get()
                
                if docs.exists:
                    
                    data = docs.to_dict()
                    r =data
                    llaves = list(r.keys())
                    for l in llaves:
                        item=r[l]
                        
                        if not isinstance(item, dict):
                            continue
                        
                        if not organizador or item['Organizador'] == organizador:
                            resultados[l]=item
                        
            print(resultados)
            return resultados
        except Exception as e:
            print(f"Error en la consulta de evento por organizador: {e}")
            return {}
    
    
    def obtener_eventos_por_organizador(self, organizador=None):
        if not self._check_db(): return {}
        try:
            query = self.db.collection("Sector")
            query2=query.document(self.sector)
            query3=query2.collection(self.fecha)
            query4=query3.document("Eventos")
            
            docs = query4.get()
            
            
            
            resultados = {}
            if docs.exists:
                
                data = docs.to_dict()
                r =data
                llaves = list(r.keys())
                for l in llaves:
                    item=r[l]
                    
                    if not isinstance(item, dict):
                        continue
                    
                    if not organizador or item['Organizador'] == organizador:
                        resultados[l]=item
                    

            return resultados
        except Exception as e:
            print(f"Error en la consulta de evento por organizador: {e}")
            return {}
        
    def obtener_informacion(self, organizador=None, fecha_inicio=None, fecha_fin=None):
        if not self._check_db(): return []
        eventos = self.obtener_eventos_por_organizador(organizador)
        
        eventos_filtrados1={}
        eventos_filtrados2={}
        eventos_filtrados3={}
        
        llaves = list(eventos.keys())
        if fecha_inicio:
            for l in llaves:
                e = evento[l]
                if e['Fechas']['Fecha_Inicio'] >= fecha_inicio:
                    eventos_filtrados1[l]=e
            eventos = eventos_filtrados1
            llaves = list(eventos_filtrados1.keys())
        
        if fecha_fin:
            for l in llaves:
                e = evento[l]
                if e['Fechas']['Fecha_Termino'] <= fecha_fin:
                    eventos_filtrados2[l]=e
            eventos = eventos_filtrados2
            llaves = list(eventos_filtrados2.keys())
                    
        for l in llaves:
            e=eventos[l]
            cantidad_v = len(e['Asistencia'])
            cal=[ev['Calificacion'] for ev in e['Asistencia']]
            calificacion_t = round((sum(cal)/cantidad_v),2)
            imagenes = [i['Direccion'] for i in e['Archivos'] if i['Tipo'] == 'Imagen']
            bloque = {
                'Titulo': e['Titulo'],
                'Descripcion': e['Descripcion'],
                'Calificacion':calificacion_t,
                'Imagenes': imagenes,
                'Ubicacion': e['Ubicacion']['Direccion'],
                'Etiquetas': e['Etiquetas'],
                'Estado': e['Estado'],
                'Fecha_Inicio': e['Fechas']['Fecha_Inicio'],
                'Fecha_Termino': e['Fechas']['Fecha_Termino']
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
        """
        Sube un nuevo evento al documento 'Eventos' de la colección de fechas.
        El evento se añade como un nuevo campo (clave:valor) dentro de ese documento.
        
        Args:
            evento_data: Diccionario con los datos del evento (Título, Organizador, etc.).
                        
        Returns:
            El ID asignado al evento si la operación fue exitosa, o None en caso contrario.
        """

        # 1. Generar un ID ÚNICO para este evento.
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
        event_id = f"Event-{timestamp_str}" 

        # 2. Construir la referencia al documento de 'Eventos'
        try:
            # Sector/{self.sector}/{self.fecha}/Eventos
            doc_ref = (self.db.collection("Sector")
                    .document(self.sector)
                    .collection(self.fecha)
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

            # 2. Construir la ruta completa del campo usando la notación de punto
            # La ruta será: "{event_id}.{campo}"
            # Esta notación le indica a Firestore que debe entrar al campo 'event_id' 
            # y modificar solo el sub-campo 'campo'.
            field_path = f"{event_id}.{campo}"
            
            payload: Dict[str, Any] = {}

            if eliminar:
                # Para eliminar, asignamos el constante DELETE_FIELD de Firestore
                payload[field_path] = DELETE_FIELD
                accion = f"Eliminando campo '{campo}'"
            else:
                # Para modificar/añadir, asignamos el nuevo valor
                if nuevo_valor is None:
                    print("⛔ Debe proporcionar un 'nuevo_valor' si no está eliminando.")
                    return False
                    
                payload[field_path] = nuevo_valor
                accion = f"Actualizando campo '{campo}' a '{nuevo_valor}'"

            # 3. Usar el método update() para aplicar la modificación
            doc_ref.update(payload)
            
            print(f"✅ Operación exitosa: {accion} en el evento ID {event_id}")
            
        except Exception as e:
            print(e)
        
        
    
    def subir_imagen(self):
        if not self._check_db(): return





        
lect=Lectura_Eventos_DB()
documento = lect.obtener_informacion('22.222.222-2')#lect.obtener_eventos_por_organizador('22.222.222-2')

#print(documento)



