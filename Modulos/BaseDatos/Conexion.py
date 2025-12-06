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
            location = geolocator.reverse((self.latitud, self.longitud), language='es', timeout=5)
            if location and 'address' in location.raw:
                direccion = location.raw['address']
                self.sector=f'{direccion.get("country", "Unknown")}_{direccion.get("state", "Unknown")}_{direccion.get("county", "Unknown")}_{direccion.get("city","Unknown")}'
            else:
                self.sector = 'Unknown'
        
        #self.sector='Chile_Biobío_Biobío_Los Ángeles'

    def _actualizar_estado_evento(self, fecha_termino_iso: str, estado_actual: str) -> str:
        """
        Actualiza el estado de un evento basándose en su fecha de término.
        
        Args:
            fecha_termino_iso: Fecha de término en formato ISO string o DD-MM-YYYY HH:MM
            estado_actual: Estado actual del evento
            
        Returns:
            Estado actualizado: 'En Espera', 'Terminado', o 'Cancelado'
        """
        # Si está cancelado, mantener ese estado
        if estado_actual == 'Cancelado':
            return 'Cancelado'
        
        try:
            fecha_termino = None
            
            # Convertir fecha a datetime según el formato
            if isinstance(fecha_termino_iso, str):
                # Formato ISO con T (ej: "2024-12-01T15:30:00")
                if 'T' in fecha_termino_iso:
                    fecha_termino = datetime.fromisoformat(fecha_termino_iso)
                # Formato DD-MM-YYYY HH:MM
                elif ' ' in fecha_termino_iso and ':' in fecha_termino_iso:
                    try:
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%d-%m-%Y %H:%M')
                    except ValueError:
                        # Intentar con formato alternativo
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%Y-%m-%d %H:%M')
                # Formato solo fecha DD-MM-YYYY
                else:
                    try:
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%d-%m-%Y')
                    except ValueError:
                        # Intentar con formato alternativo YYYY-MM-DD
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%Y-%m-%d')
            else:
                # Ya es un objeto datetime
                fecha_termino = fecha_termino_iso
            
            # Remover timezone si existe para comparación
            if hasattr(fecha_termino, 'tzinfo') and fecha_termino.tzinfo:
                fecha_termino = fecha_termino.replace(tzinfo=None)
            
            # Comparar con fecha actual
            ahora = datetime.now()
            
            if fecha_termino < ahora:
                return 'Terminado'
            else:
                return 'En Espera'
                
        except Exception as e:
            print(f"⚠️ Error al actualizar estado: {e}")
            print(f"   Fecha recibida: {fecha_termino_iso}")
            return estado_actual  # Mantener estado actual si hay error

    
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
                        if organizador:
                            # Normalizar RUTs para comparación (remover puntos y guiones)
                            def normalizar_rut(rut):
                                return rut.replace('.', '').replace('-', '').strip() if rut else ''
                            
                            org_normalizado = normalizar_rut(organizador)
                            evento_org = evento.get('Organizador', '')
                            evento_org_normalizado = normalizar_rut(evento_org)
                            
                            if evento_org_normalizado != org_normalizado:
                                # print(f"DEBUG: Evento {id_evento} descartado. Org: '{evento_org}' ({evento_org_normalizado}) != '{organizador}' ({org_normalizado})")
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
                                    # Detectar formato mixto: DD-MM-YYYYTHH:MM:SS o YYYY-MM-DDTHH:MM:SS
                                    if 'T' in val:
                                        try:
                                            # Intentar formato ISO estándar primero
                                            return datetime.fromisoformat(val)
                                        except ValueError:
                                            # Formato mixto: DD-MM-YYYYTHH:MM:SS
                                            if val.index('T') > 8:  # Posición de T indica formato DD-MM-YYYY
                                                fecha_parte, hora_parte = val.split('T')
                                                # Parsear fecha DD-MM-YYYY
                                                fecha_dt = datetime.strptime(fecha_parte, "%d-%m-%Y")
                                                # Parsear hora HH:MM:SS o HH:MM
                                                hora_parts = hora_parte.split(':')
                                                return fecha_dt.replace(
                                                    hour=int(hora_parts[0]),
                                                    minute=int(hora_parts[1]) if len(hora_parts) > 1 else 0,
                                                    second=int(hora_parts[2]) if len(hora_parts) > 2 else 0
                                                )
                                    
                                    # Handle string formats sin T
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
            
            # Actualizar estado del evento basándose en la fecha de término
            fecha_termino = fechas.get('Fecha_Termino', '')
            estado_actual = e.get('Estado', 'Desconocido')
            estado_actualizado = self._actualizar_estado_evento(fecha_termino, estado_actual)
            
            bloque = {
                'Titulo': e.get('Titulo', 'Sin Título'),
                'Descripcion': e.get('Descripcion', ''),
                'Calificacion': calificacion_t,
                'Imagenes': imagenes,
                'Ubicacion': ubicacion,
                'Etiquetas': e.get('Etiquetas', []),
                'Estado': estado_actualizado,  # Usar estado actualizado
                'Fecha_Inicio': fechas.get('Fecha_Inicio', ''),
                'Fecha_Termino': fechas.get('Fecha_Termino', ''),
                'Entrada': e.get('Acceso', {}).get('Valor',''),
                'Pre-inscripcion': e.get('Visibilidad', {}).get('Valor','')
            }
            eventos_filtrados3[l]=bloque
                     
        return eventos_filtrados3
    
    def obtener_eventos_mapa(self, organizador=None, fecha_inicio=None, fecha_fin=None, etiquetas=None, sector=None):
        """
        Obtiene eventos específicamente para mostrar en el mapa.
        Retorna eventos con información completa incluyendo coordenadas y sector.
        
        Args:
            sector (str, optional): Si se proporciona, busca eventos en este sector específico.
                                    Si es None, usa el sector calculado por ubicación actual.
        """
        if not self._check_db(): return {}
        
        # Si se especifica un sector manual, usarlo
        if sector:
            print(f"DEBUG: Cambiando sector de búsqueda a: {sector}")
            self.sector = sector
        
        try:
            eventos = self.obtener_eventos_por_fecha(organizador, fecha_inicio, fecha_fin, etiquetas)
            eventos_mapa = {}
            
            for event_id, evento in eventos.items():
                # Obtener ubicación
                ubicacion = evento.get('Ubicacion', {})
                
                # Solo incluir eventos que tengan coordenadas válidas
                if isinstance(ubicacion, dict):
                    lat = ubicacion.get('Latitud')
                    lon = ubicacion.get('Longitud')
                    
                    if lat and lon:
                        # **IMPORTANTE**: Calcular el sector usando las coordenadas del evento
                        # Usar la función existente filtrar_coordenadas
                        self.filtrar_coordenadas(lat, lon)
                        sector_evento = self.sector  # El sector calculado está en self.sector
                        
                        # Agregar el sector a la ubicación
                        ubicacion_con_sector = ubicacion.copy()
                        ubicacion_con_sector['Sector'] = sector_evento
                        
                        # Calcular calificación
                        asistencia = evento.get('Asistencia', [])
                        cantidad_v = len(asistencia)
                        
                        if cantidad_v > 0:
                            cal = [ev.get('Calificacion', 0) for ev in asistencia]
                            calificacion_t = round((sum(cal)/cantidad_v), 2)
                        else:
                            calificacion_t = 0.0
                        
                        # Obtener archivos
                        archivos = evento.get('Archivos', [])
                        imagenes = [i['Direccion'] for i in archivos if i.get('Tipo') == 'Imagen']
                        
                        # Actualizar estado del evento
                        fechas = evento.get('Fechas', {})
                        fecha_termino = fechas.get('Fecha_Termino', '')
                        estado_actual = evento.get('Estado', 'Desconocido')
                        estado_actualizado = self._actualizar_estado_evento(fecha_termino, estado_actual)
                        
                        # Obtener visibilidad
                        visibilidad = evento.get('Visibilidad', {})
                        
                        # Crear bloque de información para el mapa
                        bloque = {
                            'Titulo': evento.get('Titulo', 'Sin Título'),
                            'Descripcion': evento.get('Descripcion', ''),
                            'Calificacion': calificacion_t,
                            'Imagenes': imagenes,
                            'Ubicacion': ubicacion_con_sector,  # Incluir ubicación CON SECTOR
                            'Etiquetas': evento.get('Etiquetas', []),
                            'Estado': estado_actualizado,
                            'Fecha_Inicio': fechas.get('Fecha_Inicio', ''),
                            'Fecha_Termino': fechas.get('Fecha_Termino', ''),
                            'Visibilidad': visibilidad,
                            'Invitados': evento.get('Invitados', []),
                            'Entrada': evento.get('Acceso', {}).get('Valor',''),
                            'Pre-inscripcion': evento.get('Visibilidad', {}).get('Valor','')
                        }
                        eventos_mapa[event_id] = bloque
                        print(f"DEBUG: Evento '{bloque['Titulo']}' - Sector calculado: '{sector_evento}'")
            
            print(f"DEBUG: Total eventos encontrados: {len(eventos)}")
            print(f"Eventos con coordenadas para mapa: {len(eventos_mapa)}")
            return eventos_mapa
            
        except Exception as e:
            print(f"Error en obtener_eventos_mapa: {e}")
            import traceback
            traceback.print_exc()
            return {}
                

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
            location = geolocator.reverse((self.latitud, self.longitud), language='es', timeout=5)
            if location and 'address' in location.raw:
                direccion = location.raw['address']
                self.sector=f'{direccion.get("country", "Unknown")}_{direccion.get("state", "Unknown")}_{direccion.get("county", "Unknown")}_{direccion.get("city","Unknown")}'
            else:
                self.sector = 'Unknown'
        
        # self.sector='Chile_Biobío_Biobío_Los Ángeles'  # COMENTADO: No forzar sector

    def _actualizar_estado_evento(self, fecha_termino_iso: str, estado_actual: str) -> str:
        """
        Actualiza el estado de un evento basándose en su fecha de término.
        
        Args:
            fecha_termino_iso: Fecha de término en formato ISO string o DD-MM-YYYY HH:MM
            estado_actual: Estado actual del evento
            
        Returns:
            Estado actualizado: 'En Espera', 'Terminado', o 'Cancelado'
        """
        # Si está cancelado, mantener ese estado
        if estado_actual == 'Cancelado':
            return 'Cancelado'
        
        try:
            fecha_termino = None
            
            # Convertir fecha a datetime según el formato
            if isinstance(fecha_termino_iso, str):
                # Formato ISO con T (ej: "2024-12-01T15:30:00")
                if 'T' in fecha_termino_iso:
                    fecha_termino = datetime.fromisoformat(fecha_termino_iso)
                # Formato DD-MM-YYYY HH:MM
                elif ' ' in fecha_termino_iso and ':' in fecha_termino_iso:
                    try:
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%d-%m-%Y %H:%M')
                    except ValueError:
                        # Intentar con formato alternativo
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%Y-%m-%d %H:%M')
                # Formato solo fecha DD-MM-YYYY
                else:
                    try:
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%d-%m-%Y')
                    except ValueError:
                        # Intentar con formato alternativo YYYY-MM-DD
                        fecha_termino = datetime.strptime(fecha_termino_iso, '%Y-%m-%d')
            else:
                # Ya es un objeto datetime
                fecha_termino = fecha_termino_iso
            
            # Remover timezone si existe para comparación
            if hasattr(fecha_termino, 'tzinfo') and fecha_termino.tzinfo:
                fecha_termino = fecha_termino.replace(tzinfo=None)
            
            # Comparar con fecha actual
            ahora = datetime.now()
            
            if fecha_termino < ahora:
                return 'Terminado'
            else:
                return 'En Espera'
                
        except Exception as e:
            print(f"⚠️ Error al actualizar estado: {e}")
            print(f"   Fecha recibida: {fecha_termino_iso}")
            return estado_actual  # Mantener estado actual si hay error

    def subir_evento(self, evento_data: Dict[str, Any]):
        if not self._check_db(): return

        # 1. **NUEVO**: Extraer coordenadas del evento y calcular sector automáticamente
        ubicacion = evento_data.get('Ubicacion', {})
        if isinstance(ubicacion, dict):
            lat = ubicacion.get('Latitud')
            lon = ubicacion.get('Longitud')
            
            if lat and lon:
                # Usar filtrar_coordenadas para calcular el sector del evento
                print(f"📍 Calculando sector desde coordenadas: ({lat}, {lon})")
                self.filtrar_coordenadas(lat, lon)
                print(f"✅ Sector calculado: {self.sector}")
            else:
                print("⚠️ Evento sin coordenadas, usando sector por defecto")
        else:
            print("⚠️ Ubicación no válida, usando sector por defecto")

        # 2. Obtener la fecha de término (viene en formato ISO string)
        fecha_termino_iso = evento_data['Fechas']['Fecha_Termino']
        
        # 3. Convertir el string ISO a objeto datetime
        try:
            # Manejar formato ISO (ej: "2024-12-01T15:30:00")
            if isinstance(fecha_termino_iso, str):
                if 'T' in fecha_termino_iso:
                    fecha_termino_dt = datetime.fromisoformat(fecha_termino_iso)
                else:
                    # Formato alternativo DD-MM-YYYY
                    fecha_termino_dt = datetime.strptime(fecha_termino_iso, '%d-%m-%Y')
            else:
                fecha_termino_dt = fecha_termino_iso
                
        except Exception as e:
            print(f"❌ Error al parsear fecha de término: {e}")
            print(f"   Fecha recibida: {fecha_termino_iso}")
            return
                
        # 4. Extraer año y mes del objeto datetime
        año = fecha_termino_dt.year
        mes = fecha_termino_dt.month
                
        # 5. Crear un objeto datetime con el día forzado a 1 (para nombre de colección)
        fecha_primer_dia = datetime(año, mes, 1)

        # 6. Convertir a string para usar como nombre de colección
        timestamp_str = fecha_primer_dia.strftime('%d-%m-%Y')
                
        # 7. Generar el ID único del evento
        fecha_id_str = fecha_termino_dt.strftime('%Y%m%d%H%M')
        event_id = f"Event-{random.randint(0, 1000)}-{fecha_id_str}"

        # 8. Actualizar el estado del evento basándose en la fecha
        estado_actual = evento_data.get('Estado', 'En Espera')
        evento_data['Estado'] = self._actualizar_estado_evento(fecha_termino_iso, estado_actual)

        # 9. Construir la referencia al documento de 'Eventos'
        try:
            # **NUEVO**: Verificar si el sector existe, si no, crearlo
            sector_ref = self.db.collection("Sector").document(self.sector)
            
            # Verificar si el documento del sector existe
            if not sector_ref.get().exists:
                print(f"📁 Sector '{self.sector}' no existe. Creándolo...")
                # Crear el documento del sector con datos iniciales
                sector_ref.set({
                    'created_at': datetime.now(),
                    'nombre': self.sector
                })
                print(f"✅ Sector '{self.sector}' creado exitosamente")
            
            # Sector/{self.sector}/'01-mes-año'/Eventos
            doc_ref = (self.db.collection("Sector")
                      .document(self.sector)
                      .collection(f'{timestamp_str}')
                      .document("Eventos"))
                    
            # 10. Preparar el payload: {event_id: evento_data}
            payload = {
                event_id: evento_data
            }

            # 11. Usar set con merge=True para añadir el nuevo campo sin sobrescribir
            doc_ref.set(payload, merge=True)
            
            print(f"✅ Evento '{evento_data.get('Titulo', 'Sin Título')}' subido con éxito.")
            print(f"   ID asignado: {event_id}")
            print(f"   Sector: {self.sector}")
            print(f"   Estado: {evento_data['Estado']}")
            return True

        except Exception as e:
            print(f"❌ Error al intentar subir el evento: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def agregar_archivo_evento(self, event_id: str, archivo_data: Dict[str, Any]):
        """
        Agrega un archivo (imagen) a la lista de Archivos de un evento.
        
        Args:
            event_id: ID del evento
            archivo_data: Diccionario con Direccion, Extencion, Tipo, Ubicacion
        """
        if not self._check_db(): 
            print("❌ Base de datos no disponible")
            return
        
        try:
            # Buscar el evento en todas las colecciones de meses
            doc_sector = self.db.collection("Sector").document(self.sector)
            colecciones_meses = list(doc_sector.collections())
            
            for col in colecciones_meses:
                doc_ref = col.document("Eventos")
                doc = doc_ref.get()
                
                if doc.exists:
                    data = doc.to_dict()
                    if event_id in data:
                        # Obtener archivos actuales
                        archivos_actuales = data[event_id].get('Archivos', [])
                        
                        # Agregar nuevo archivo
                        archivos_actuales.append(archivo_data)
                        
                        # Actualizar en Firestore usando notación de punto
                        doc_ref.update({
                            f"{event_id}.Archivos": archivos_actuales
                        })
                        
                        print(f"✅ Archivo agregado al evento {event_id}")
                        print(f"   Dirección: {archivo_data['Direccion']}")
                        return
            
            print(f"❌ Evento {event_id} no encontrado en ninguna colección")
            
        except Exception as e:
            print(f"❌ Error al agregar archivo al evento: {e}")
            import traceback
            traceback.print_exc()
    
    def cambiar_estado_evento(self, event_id: str, nuevo_estado: str):
        """
        Cambia el estado de un evento.
        
        Args:
            event_id: ID del evento
            nuevo_estado: Nuevo estado ('En Espera', 'Terminado', 'Cancelado')
        """
        if not self._check_db(): 
            print("❌ Base de datos no disponible")
            return
        
        try:
            # Buscar el evento en todas las colecciones de meses
            doc_sector = self.db.collection("Sector").document(self.sector)
            colecciones_meses = list(doc_sector.collections())
            
            for col in colecciones_meses:
                doc_ref = col.document("Eventos")
                doc = doc_ref.get()
                
                if doc.exists:
                    data = doc.to_dict()
                    if event_id in data:
                        # Actualizar estado en Firestore
                        doc_ref.update({
                            f"{event_id}.Estado": nuevo_estado
                        })
                        
                        print(f"✅ Estado del evento {event_id} cambiado a: {nuevo_estado}")
                        return
            
            print(f"❌ Evento {event_id} no encontrado en ninguna colección")
            
        except Exception as e:
            print(f"❌ Error al cambiar estado del evento: {e}")
            import traceback
            traceback.print_exc()
    
    def actualizar_etiquetas_evento(self, event_id: str, etiqueta: str, agregar: bool):
        """
        Agrega o remueve una etiqueta de un evento.
        
        Args:
            event_id: ID del evento
            etiqueta: Nombre de la etiqueta
            agregar: True para agregar, False para remover
        """
        if not self._check_db(): 
            print("❌ Base de datos no disponible")
            return
        
        try:
            # Buscar el evento en todas las colecciones de meses
            doc_sector = self.db.collection("Sector").document(self.sector)
            colecciones_meses = list(doc_sector.collections())
            
            for col in colecciones_meses:
                doc_ref = col.document("Eventos")
                doc = doc_ref.get()
                
                if doc.exists:
                    data = doc.to_dict()
                    if event_id in data:
                        # Obtener etiquetas actuales
                        etiquetas_actuales = data[event_id].get('Etiquetas', [])
                        
                        if agregar:
                            # Agregar etiqueta si no existe
                            if etiqueta not in etiquetas_actuales:
                                etiquetas_actuales.append(etiqueta)
                                accion = "agregada"
                            else:
                                return  # Ya existe, no hacer nada
                        else:
                            # Remover etiqueta si existe
                            if etiqueta in etiquetas_actuales:
                                etiquetas_actuales.remove(etiqueta)
                                accion = "removida"
                            else:
                                return  # No existe, no hacer nada
                        
                        # Actualizar en Firestore
                        doc_ref.update({
                            f"{event_id}.Etiquetas": etiquetas_actuales
                        })
                        
                        print(f"✅ Etiqueta '{etiqueta}' {accion} del evento {event_id}")
                        return
            
            print(f"❌ Evento {event_id} no encontrado")
            
        except Exception as e:
            print(f"❌ Error al actualizar etiquetas: {e}")
            import traceback
            traceback.print_exc()
    
    def actualizar_evento_completo(self, event_id: str, cambios: Dict[str, Any]):
        """
        Actualiza múltiples campos de un evento.
        
        Args:
            event_id: ID del evento
            cambios: Diccionario con los campos a actualizar
        """
        if not self._check_db(): 
            print("❌ Base de datos no disponible")
            return
        
        try:
            # Buscar el evento en todas las colecciones de meses
            doc_sector = self.db.collection("Sector").document(self.sector)
            colecciones_meses = list(doc_sector.collections())
            
            for col in colecciones_meses:
                doc_ref = col.document("Eventos")
                doc = doc_ref.get()
                
                if doc.exists:
                    data = doc.to_dict()
                    if event_id in data:
                        # Preparar actualizaciones
                        updates = {}
                        
                        for campo, valor in cambios.items():
                            # Manejar campos anidados (ej: "Fechas.Fecha_Inicio")
                            if '.' in campo:
                                # Para campos anidados, necesitamos actualizar el objeto completo
                                partes = campo.split('.')
                                if partes[0] == 'Fechas':
                                    # Obtener fechas actuales
                                    fechas_actuales = data[event_id].get('Fechas', {})
                                    fechas_actuales[partes[1]] = valor
                                    updates[f"{event_id}.Fechas"] = fechas_actuales
                                elif partes[0] in ['Acceso', 'Visibilidad']:
                                    # Manejar Acceso y Visibilidad
                                    actual = data[event_id].get(partes[0], {})
                                    actual[partes[1]] = valor
                                    updates[f"{event_id}.{partes[0]}"] = actual
                            else:
                                # Campo simple
                                updates[f"{event_id}.{campo}"] = valor
                        
                        # Actualizar en Firestore
                        if updates:
                            doc_ref.update(updates)
                            print(f"✅ Evento {event_id} actualizado:")
                            for campo in cambios.keys():
                                print(f"   - {campo}")
                        
                        return
            
            print(f"❌ Evento {event_id} no encontrado")
            
        except Exception as e:
            print(f"❌ Error al actualizar evento: {e}")
            import traceback
            traceback.print_exc()
    
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



