import os
import shutil
import logging
from functools import partial
from pathlib import Path
from datetime import datetime, timedelta

# --- KIVY IMPORTS ---
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.modalview import ModalView
from kivy.properties import (
    NumericProperty, ObjectProperty, BooleanProperty, StringProperty
)
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform
from kivy.factory import Factory

from Modulos.Singleton.Perfil import Singleton_Perfil
from Modulos.BaseDatos.Conexion import Lectura_Eventos_DB
from Modulos.BaseDatos.Ubicacion import LocationService

# --- GARDEN / EXTERNAL IMPORTS ---
from kivy_garden.mapview import MapView, MapMarkerPopup

# Intentar importar plyer.gps solo si es necesario
try:
    from plyer import gps
except ImportError:
    gps = None
    
# --- CONFIGURACIÓN GLOBAL ---
LOG_LEVEL_KIVY = logging.WARNING
LOG_LEVEL_URL = logging.WARNING

logging.getLogger('urllib3.connectionpool').setLevel(LOG_LEVEL_URL)
logging.getLogger('kivy').setLevel(LOG_LEVEL_KIVY)
os.environ['KIVY_NO_FILELOG'] = '1'
os.environ['KIVY_NO_CONSOLELOG'] = '1'


# --- CLASES DE WIDGETS (Reutilizadas de BAA_Mapa) ---
class ElementoEstrella(Widget):
    t = NumericProperty(50.0) 
    r = NumericProperty(20.0) 
    porcentaje_visible = NumericProperty(0.5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._actualizar_radios) 
        
    def _actualizar_radios(self, instance, value):
        if self.width > 0 and self.height > 0:
            self.t = min(self.width, self.height) * 0.45
            self.r = self.t * 0.4
    
    def calificar(self, evento_id, calificacion):
        pass

class Menu_Evento_Informacion(BoxLayout):
    descrip = StringProperty('')
    calificacion = NumericProperty(0)


class Menu_Evento_Base(ModalView):
    titulo = StringProperty("Titulo por defecto")
    pestana = StringProperty("imagen")
    contenido_nombre = StringProperty("")

    def Cargar_Interfaz_Imagenes(self):
        if 'caja_contenido' not in self.ids:
            return
        
        try:
            contenedor = self.ids.caja_contenido
            contenedor.clear_widgets()
            
            if self.contenido_nombre:
                nuevo_widget = Factory.get(self.contenido_nombre)()
                contenedor.add_widget(nuevo_widget)
            
            self.pestana = 'imagen'
        except (AttributeError, ReferenceError):
            return

    def Cargar_Interfaz_Informacion(self):
        if 'caja_contenido' not in self.ids:
            return

        try:
            self.ids.caja_contenido.clear_widgets()
            
            interfaz = Menu_Evento_Informacion()
            interfaz.titulo = self.titulo
            interfaz.texto = self.descripcion
            interfaz.ubicacion = self.ubicacion
            interfaz.calificacion = self.calificacion
            
            if 'lista_etiquetas' in interfaz.ids:
                for tag in self.etiquetas:
                    et = Factory.Etiqueta_Evento()
                    et.texto = tag
                    et.altura = 50
                    interfaz.ids.lista_etiquetas.add_widget(et)
            
            self.ids.caja_contenido.add_widget(interfaz)
            self.pestana = 'info'
        except (AttributeError, ReferenceError):
            return
    
    def Cargar_Interfaz_ListaCompras(self):
        if 'caja_contenido' not in self.ids:
            return
            
        try:
            self.ids.caja_contenido.clear_widgets()
            Shop = Factory.Menu_Evento_ListaCompra()
            self.ids.caja_contenido.add_widget(Shop)
            self.pestana = 'shop'
        except (AttributeError, ReferenceError):
            return


class Miniatura_Evento(MapMarkerPopup):
    title = StringProperty('Título de Evento')
    tiempo = StringProperty("15d")
    action = ObjectProperty(None, allownone=True)
    marker_source = StringProperty('atlas://map_icons/pin')


class Layout_Mapa(FloatLayout):
    """Widget principal que contiene el MapView y maneja la lógica de ubicación/marcadores."""

    # --- PROPIEDADES ---
    LAT_DEFAULT = -33.4569400  # Santiago, Chile
    LON_DEFAULT = -70.6482700
    
    latitud = NumericProperty(LAT_DEFAULT)
    longitud = NumericProperty(LON_DEFAULT)
    zoom = NumericProperty(12)
    marker = ObjectProperty(None, allownone=True)
    ubicacion_actualizada = BooleanProperty(False)
    show_filters = BooleanProperty(False)  # NUEVO: Para controlar visibilidad de filtros
    
    # Referencias a los relojes
    _reloj_inicio = ObjectProperty(None, allownone=True)
    _reloj_cache = ObjectProperty(None, allownone=True)
    _reloj_ubicacion = ObjectProperty(None, allownone=True)  # NUEVO: Para actualización periódica
    _reloj_timers = ObjectProperty(None, allownone=True)  # NUEVO: Para actualizar contadores de eventos
    _gps_timeout_ev = ObjectProperty(None, allownone=True)

    # --- INICIALIZACIÓN ---
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super().__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        self._reloj_inicio = None
        self._reloj_cache = None
        self._reloj_ubicacion = None
        self._reloj_timers = None  # NUEVO: Para actualizar contadores
        self._gps_timeout_ev = None
        self.marcadores_eventos = {}  # Diccionario para rastrear marcadores de eventos
        self.eventos_data = {}  # NUEVO: Guardar datos de eventos para actualizar timers
        
        # Filtros (NO se actualizan automáticamente)
        self.sector_actual = None
        self.filtro_etiqueta_actual = 'Todas'
        self.filtro_mes_actual = 'Todos'
        
    def get_map_view(self):
        """Busca la instancia de MapView dentro del contenedor 'mapa'."""
        map_container = self.ids.get('mapa') 
        
        if map_container and map_container.children:
            from kivy_garden.mapview import MapView
            for child in map_container.children:
                # Primero intentar obtener MapView directamente
                if isinstance(child, MapView): 
                    return child
                # Si es AgregarMapa, buscar MapView dentro de él
                if hasattr(child, 'children'):
                    for subchild in child.children:
                        if isinstance(subchild, MapView):
                            return subchild
        
        return None

    # --- CICLO DE VIDA ---

    def Iniciar_Ventana(self):
        print("Iniciando BBA_Mapa...")
    
        # 1. Limpia y REMUEVE la instancia anterior (pero preserva el marcador de usuario)
        self.limpiar_mapa_profundamente() 
        
        # 2. CREAR Y AÑADIR LA NUEVA INSTANCIA DE MAPVIEW
        map_container = self.ids.get('mapa')
        if not map_container:
            print("ERROR: Contenedor 'mapa' (id) no encontrado en el layout.")
            return

        new_map_view = Factory.AgregarMapa(
            lat=self.latitud,
            lon=self.longitud,
            zoom=self.zoom
        )
        
        map_container.add_widget(new_map_view)
        print("Nueva instancia de MapView añadida y lista.")

        # 3. INICIALIZAR LÓGICA (timers, etc.)
        self.buscar_y_limpiar_cache() 
        
        self._reloj_inicio = Clock.schedule_once(self._initialize_location_task, 2)
        self._reloj_cache = Clock.schedule_interval(self.limpiar_cache, 5)
        
        # 4. NUEVO: Iniciar actualización periódica de ubicación (cada 10 segundos)
        self._reloj_ubicacion = Clock.schedule_interval(self._actualizar_ubicacion_periodica, 10)
        
        # 5. NUEVO: Iniciar actualización de contadores de eventos (cada 60 segundos)
        self._reloj_timers = Clock.schedule_interval(self._actualizar_timers_eventos, 60)
        
        # 6. Calcular sector inicial (SOLO UNA VEZ al abrir el mapa)
        Clock.schedule_once(lambda dt: self._calcular_sector_inicial(), 2.5)
        
        # 7. Si ya existe un marcador de usuario, volver a agregarlo al nuevo mapa
        if self.marker and self.latitud and self.longitud:
            Clock.schedule_once(lambda dt: self._readd_user_marker(), 0.5)
        
        # 8. Cargar eventos después de un breve delay
        Clock.schedule_once(lambda dt: self.cargar_eventos(), 3)
        
        print("BBA_Mapa inicializado")
    
    def _readd_user_marker(self):
        """Re-agrega el marcador de usuario al mapa cuando se vuelve a entrar."""
        map_view = self.get_map_view()
        if map_view and self.marker:
            try:
                # Eliminar el marcador antiguo si existe
                if self.marker in map_view.markers:
                    map_view.remove_marker(self.marker)
                
                # Crear un nuevo marcador con la última ubicación conocida
                self.marker = self.Agregar_Marcador(
                    lat=self.latitud,
                    lon=self.longitud,
                    title="Mi Ubicación",
                    callback=None,
                    source_img='Static\\Imagenes\\actual_ubicacion.png',
                    es_usuario=True
                )
                print(f"Marcador de usuario re-agregado en: {self.latitud}, {self.longitud}")
            except Exception as e:
                print(f"Error al re-agregar marcador de usuario: {e}")

    def stop_gps(self):
        """Detiene la escucha del GPS y cancela el timeout."""
        if self._gps_timeout_ev:
            try: self._gps_timeout_ev.cancel()
            except Exception: pass
            self._gps_timeout_ev = None
            
        if platform == "android":
            if gps:
                try: 
                    gps.stop()
                    print("Servicio GPS detenido en Android.")
                except Exception as e: 
                    print(f"Error al detener GPS en Android: {e}")
    
    def Cerrar_Ventana(self):
        """Limpia todos los recursos al salir de la pantalla."""
        print("Cerrando BBA_Mapa...")
        self.stop_gps()
        
        # NUEVO: Cancelar actualización periódica de ubicación
        if self._reloj_ubicacion:
            self._reloj_ubicacion.cancel()
            self._reloj_ubicacion = None
        
        # NUEVO: Cancelar actualización de timers de eventos
        if self._reloj_timers:
            self._reloj_timers.cancel()
            self._reloj_timers = None
        
        self.limpiar_mapa_profundamente()

    # --- LIMPIEZA PROFUNDA ---
    def limpiar_mapa_profundamente(self):
        """Limpia completamente el MapView y lo remueve del layout de forma segura."""
        map_view = self.get_map_view()

        # 1. Cancelar Clocks
        if self._reloj_inicio:
            self._reloj_inicio.cancel()
        if self._reloj_cache:
            self._reloj_cache.cancel()
        if self._reloj_ubicacion:
            self._reloj_ubicacion.cancel()
        if self._reloj_timers:
            self._reloj_timers.cancel()
            
        # 2. LIMPIEZA Y REMOCIÓN DEL WIDGET
        if map_view:
            if hasattr(map_view, 'stop_downloading'):
                map_view.stop_downloading() 
            
            map_view._pause = True 
            
            # IMPORTANTE: NO eliminar el marcador del usuario para que persista
            if hasattr(map_view, 'markers'):
                for marker in list(map_view.markers):
                    # Solo eliminar marcadores que NO sean el marcador del usuario
                    if marker != self.marker:
                        map_view.remove_marker(marker)
            
            if map_view.parent:
                map_view.parent.remove_widget(map_view)
            
            print("MapView retirado del layout.")

    # --- MARCADORES ---

    def Agregar_Marcador(self, lat, lon, title="Lugar", callback=None, source_img=None, es_usuario=False, event_id=None):
        """Agrega un MapMarker al mapa."""
        map_view = self.get_map_view()
        if not map_view:
            print("No se encontró map_view.")
            return None
        
        try:
            # Si es el marcador del usuario, usar MapMarker simple con imagen personalizada
            if es_usuario:
                from kivy_garden.mapview import MapMarker
                marker = MapMarker(
                    lat=lat, 
                    lon=lon,
                    source=source_img if source_img else 'Static\\Imagenes\\actual_ubicacion.png'
                )
                # Hacer el marcador completamente invisible - solo la imagen se verá
                marker.size_hint = (None, None)
                marker.size = (1, 1)  # Tamaño mínimo
                marker.opacity = 0  # Completamente invisible
                marker.disabled = True  # Deshabilitado para que no interfiera
                print(f"Marcador de usuario creado (invisible) con imagen: {source_img}")
            else:
                # Para eventos, usar Miniatura_Evento con popup
                marker = Factory.Miniatura_Evento(
                    lat=lat, 
                    lon=lon, 
                    title=title, 
                    marker_source=source_img if source_img else 'atlas://map_icons/pin'
                )
                
                if callback:
                    marker.action = callback
                
                # Agregar ID del evento al marcador para rastrearlo
                if event_id:
                    marker.event_id = event_id
            
            map_view.add_marker(marker)
            print(f"Marcador agregado. Total marcadores en MapView: {len(map_view.markers) if hasattr(map_view, 'markers') else 'N/A'}")
            return marker
            
        except Exception as e:
            print(f"Error al agregar marcador: {e}")
            import traceback
            traceback.print_exc()
            return None

    def Eliminar_marcador(self, marker):
        """Elimina un marcador específico del mapa."""
        map_view = self.get_map_view()
        if map_view and marker:
            try:
                map_view.remove_marker(marker)
                return True
            except Exception as e:
                print(f"Error al eliminar marcador: {e}")
        return False

    # --- GESTIÓN DE CACHÉ ---
    
    def buscar_y_limpiar_cache(self):
        """Limpia de forma segura los archivos de caché de MapView."""
        try:
            cache_dir = Path(os.getcwd()) / 'cache'
            
            if cache_dir.exists():
                cache_files = []
                for file_path in cache_dir.glob('custom_map_*'):
                    cache_files.append((file_path.stat().st_mtime, file_path))
                
                cache_files.sort(key=lambda x: x[0], reverse=True)
                
                for _, file_path in cache_files[12:]: 
                    try:
                        file_path.unlink()
                    except Exception as e:
                        print(f"Advertencia: No se pudo eliminar caché: {file_path} - {e}")
            return True
            
        except Exception as e:
            print(f"Error durante la gestión del caché: {e}")
            return False

    def limpiar_cache(self, dt):
        """Tarea programada para limpiar el caché periódicamente."""
        self.buscar_y_limpiar_cache()
       
    # --- GEOLOCALIZACIÓN ---
    
    def _initialize_location_task(self, dt):
        """Inicia la tarea de obtención de ubicación."""
        self.get_location_once()
        
    def request_android_permissions(self):
        """Solicita permisos de ubicación en Android."""
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION])
            except Exception:
                pass
        
    def get_location_once(self, timeout=15):
        """Decide si usar GPS (Android) o IP (PC)."""
        if platform == "android" and gps:
            self.request_android_permissions()
            try:
                gps.configure(on_location=self._on_location, on_status=self._on_status)
                gps.start(minTime=1000, minDistance=5) 
                
                self._gps_timeout_ev = Clock.schedule_once(self._on_gps_timeout, timeout)
            except NotImplementedError:
                self._get_location_by_ip()
        else:
            self._get_location_by_ip()

    def _on_gps_timeout(self, dt):
        """Se ejecuta si el GPS no responde a tiempo."""
        print("Timeout: no se obtuvo ubicación por GPS.")
        if gps:
            try: gps.stop()
            except Exception: pass
        self._get_location_by_ip()
        
    def _get_location_by_ip(self):
        """Obtiene la ubicación usando una API de geolocalización por IP."""
        url = "http://ip-api.com/json/"
        
        req = UrlRequest(
            url,
            on_success=partial(self._process_ip_location, default=False),
            on_error=partial(self._process_ip_location, default=True),
            on_failure=partial(self._process_ip_location, default=True),
            timeout=15
        )

    def _process_ip_location(self, req, result, default=False):
        """Callback centralizado para procesar la respuesta de la API de IP."""
        if default or req.resp_status != 200:
            print("Fallo la solicitud de IP. Usando ubicación por defecto.")
            self._on_location(lat=self.LAT_DEFAULT, lon=self.LON_DEFAULT)
            return

        try:
            location_data = {
                'lat': result.get('lat', result.get('latitude')),
                'lon': result.get('lon', result.get('longitude')),
                'city': result.get('city'),
                'region': result.get('regionName'),
                'country': result.get('country')
            }
            self._on_location(**location_data)
        except Exception as e:
            print(f"Error procesando respuesta de IP: {e}")
            self._on_location(lat=self.LAT_DEFAULT, lon=self.LON_DEFAULT)
            
    def _on_location(self, **kwargs):
        """Actualiza la UI con la nueva ubicación (GPS o IP)."""
        if self._gps_timeout_ev:
            try: self._gps_timeout_ev.cancel()
            except Exception: pass
            
        try:
            lat = float(kwargs.get('lat', self.LAT_DEFAULT))
            lon = float(kwargs.get('lon', self.LON_DEFAULT))
            
            if lat and lon:
                self.latitud = lat
                self.longitud = lon
                self.zoom = 15
                self.ubicacion_actualizada = True
                
                self.mover_marcador_usuario(lat, lon) 
                
                print(f"Ubicación actualizada: {lat}, {lon}")
                                
        except Exception as e:
            print(f"Error en _on_location: {e}")

    def _actualizar_ubicacion_periodica(self, dt):
        """NUEVO: Actualiza la ubicación del usuario periódicamente usando LocationService."""
        try:
            location_service = LocationService()
            ubicacion = location_service.obtener_mi_ubicacion()
            
            if ubicacion['latitud'] and ubicacion['longitud']:
                self.latitud = ubicacion['latitud']
                self.longitud = ubicacion['longitud']
                # NO centrar el mapa automáticamente en actualizaciones periódicas
                self.mover_marcador_usuario(self.latitud, self.longitud, centrar=False)
                print(f"Ubicación actualizada periódicamente: {self.latitud}, {self.longitud}")
        except Exception as e:
            print(f"Error en actualización periódica de ubicación: {e}")

    def mover_marcador_usuario(self, lat, lon, centrar=True):
        """Mueve el marcador de usuario y opcionalmente centra el mapa en él."""
        map_view = self.get_map_view()
        
        if map_view:
            if self.marker:
                # Actualizar la posición del marcador existente
                self.marker.lat = lat
                self.marker.lon = lon
                print(f"Marcador de usuario movido a: {lat}, {lon}")
            else:
                # Crear el marcador por primera vez con imagen personalizada
                self.marker = self.Agregar_Marcador(
                    lat=lat, 
                    lon=lon, 
                    title="Mi Ubicación",
                    callback=None,  # Sin callback para evitar popup
                    source_img='Static\\Imagenes\\actual_ubicacion.png',
                    es_usuario=True  # Marcar como usuario para usar MapMarker simple
                )
                print(f"Marcador de usuario creado en: {lat}, {lon}")
            
            # Solo centrar el mapa en la primera ubicación o si se solicita explícitamente
            if centrar:
                map_view.center_on(lat, lon)
        else:
            self.latitud = lat
            self.longitud = lon
    
    def _calcular_sector_inicial(self):
        """Calcula el sector SOLO al abrir el mapa (no en cada actualización)."""
        if self.latitud and self.longitud:
            self._calcular_sector_usuario(self.latitud, self.longitud)
    
    def _calcular_sector_usuario(self, lat, lon):
        """Calcula el sector del usuario usando geocodificación inversa."""
        try:
            from geopy.geocoders import Nominatim
            
            geolocator = Nominatim(user_agent="buzzevent_map")
            location = geolocator.reverse((lat, lon), language='es')
            
            if location and 'address' in location.raw:
                direccion = location.raw['address']
                country = direccion.get('country', 'Unknown')
                state = direccion.get('state', 'Unknown')
                county = direccion.get('county', 'Unknown')
                city = direccion.get('city', 'Unknown')
                
                self.sector_actual = f"{country}_{state}_{county}_{city}"
                
                # Actualizar label de sector en la UI
                if 'label_sector' in self.ids:
                    ciudad = direccion.get('city', direccion.get('town', direccion.get('village', 'Desconocido')))
                    self.ids.label_sector.text = f'Sector: {ciudad}'
                
                print(f"Sector calculado: {self.sector_actual}")
                
                # Aplicar filtros SOLO la primera vez
                self.aplicar_filtros()
            else:
                self.sector_actual = 'Unknown'
                if 'label_sector' in self.ids:
                    self.ids.label_sector.text = 'Sector: Desconocido'
        except Exception as e:
            print(f"Error calculando sector: {e}")
            self.sector_actual = 'Unknown'
            if 'label_sector' in self.ids:
                self.ids.label_sector.text = 'Sector: Error'

    def _on_status(self, stype, status):
        """Maneja el estado del GPS (opcional)."""
        pass

    # --- CARGA Y FILTRADO DE EVENTOS ---
    
    def cargar_eventos(self):
        """NUEVO: Carga y filtra eventos del mapa según los criterios especificados."""
        try:
            print("Cargando eventos en el mapa...")
            
            # Obtener RUT del usuario
            perfil = Singleton_Perfil.get_instance()
            rut_usuario = perfil.rut if perfil else None
            
            # Obtener todos los eventos usando el método específico para el mapa
            db = Lectura_Eventos_DB()
            if hasattr(db, 'obtener_eventos_mapa'):
                # Pasar el sector actual para que busque en el lugar correcto
                print(f"Consultando DB para sector: {self.sector_actual}")
                eventos = db.obtener_eventos_mapa(sector=self.sector_actual)
            else:
                eventos = db.obtener_informacion()
            
            # Aplicar filtros
            eventos_filtrados = self._aplicar_filtros_eventos(eventos)
            
            ahora = datetime.now()
            eventos_agregados = 0
            
            for event_id, evento in eventos_filtrados.items():
                # Obtener datos del evento
                visibilidad = evento.get('Visibilidad', {})
                if isinstance(visibilidad, dict):
                    tipo_visibilidad = visibilidad.get('Tipo', 'Publico')
                else:
                    tipo_visibilidad = 'Publico'
                
                estado = evento.get('Estado', 'Desconocido')
                
                # FILTRO 1: Eventos Públicos en Espera
                if tipo_visibilidad == 'Publico' and estado == 'En Espera':
                    self._agregar_marcador_evento(evento, event_id)
                    eventos_agregados += 1
                    continue
                
                # FILTRO 2: Eventos Terminados recientes (< 15 min)
                if estado == 'Terminado':
                    fecha_termino_str = evento.get('Fecha_Termino', '')
                    try:
                        fecha_termino = self._parsear_fecha(fecha_termino_str)
                        if fecha_termino:
                            diferencia = ahora - fecha_termino
                            
                            if diferencia < timedelta(minutes=15):
                                self._agregar_marcador_evento(evento, event_id)
                                eventos_agregados += 1
                                continue
                    except Exception as e:
                        print(f"Error parseando fecha de evento {event_id}: {e}")
                
                # FILTRO 3: Eventos Privados donde el usuario es invitado
                if tipo_visibilidad == 'Privado' and rut_usuario:
                    invitados = evento.get('Invitados', [])
                    rut_normalizado = rut_usuario.replace('.', '').replace('-', '').strip()
                    
                    for invitado in invitados:
                        if isinstance(invitado, dict):
                            invitado_rut = invitado.get('RUT', '')
                        else:
                            invitado_rut = str(invitado)
                        
                        invitado_normalizado = invitado_rut.replace('.', '').replace('-', '').strip()
                        
                        if rut_normalizado == invitado_normalizado:
                            self._agregar_marcador_evento(evento, event_id)
                            eventos_agregados += 1
                            break
            
            print(f"Total de eventos agregados al mapa: {eventos_agregados}")
            
        except Exception as e:
            print(f"Error al cargar eventos: {e}")
            import traceback
            traceback.print_exc()

    def _parsear_fecha(self, fecha_str):
        """Parsea una fecha en diferentes formatos."""
        if not fecha_str:
            return None
        
        try:
            # Formato ISO con T
            if 'T' in str(fecha_str):
                return datetime.fromisoformat(str(fecha_str).replace('Z', ''))
            # Formato DD-MM-YYYY HH:MM
            elif ' ' in str(fecha_str) and ':' in str(fecha_str):
                try:
                    return datetime.strptime(str(fecha_str), '%d-%m-%Y %H:%M')
                except ValueError:
                    return datetime.strptime(str(fecha_str), '%Y-%m-%d %H:%M')
            # Formato solo fecha
            else:
                try:
                    return datetime.strptime(str(fecha_str), '%d-%m-%Y')
                except ValueError:
                    return datetime.strptime(str(fecha_str), '%Y-%m-%d')
        except Exception as e:
            print(f"Error parseando fecha '{fecha_str}': {e}")
            return None

    def _agregar_marcador_evento(self, evento, event_id):
        """Agrega un marcador de evento al mapa con estado y tiempo."""
        ubicacion = evento.get('Ubicacion', {})
        
        # Manejar diferentes formatos de ubicación
        if isinstance(ubicacion, dict):
            lat = ubicacion.get('Latitud')
            lon = ubicacion.get('Longitud')
        elif isinstance(ubicacion, str):
            # Si es una dirección de texto, no podemos agregar marcador
            return
        else:
            return
        
        if lat and lon:
            try:
                titulo = evento.get('Titulo', 'Evento')
                estado = evento.get('Estado', 'En Espera')
                
                # Calcular el estado y tiempo del evento estilo Pokemon GO
                estado_info = self._calcular_estado_evento(evento)
                tiempo_texto = estado_info['tiempo_texto']
                color_fondo = estado_info['color']
                
                # Determinar imagen según estado
                if estado == 'Terminado':
                    source_img = 'Static\\Imagenes\\eventolisto.png'
                elif estado == 'Cancelado':
                    source_img = 'Static\\Imagenes\\eventocancelado.png'
                else:
                    source_img = 'atlas://map_icons/pin'
                
                marker = self.Agregar_Marcador(
                    lat=float(lat),
                    lon=float(lon),
                    title=titulo,
                    callback=lambda *args: self._abrir_detalle_evento(event_id, evento),
                    source_img=source_img,
                    event_id=event_id  # IMPORTANTE: Pasar el event_id para rastreo
                )
                
                if marker:
                    # Actualizar el tiempo del marcador
                    marker.tiempo = tiempo_texto
                    self.marcadores_eventos[event_id] = marker
                    # Guardar datos del evento para actualizar timers
                    self.eventos_data[event_id] = evento
                    print(f"Marcador de evento agregado: {event_id} - {titulo}")
                    
            except Exception as e:
                print(f"Error agregando marcador para evento {event_id}: {e}")
    
    def _calcular_estado_evento(self, evento):
        """Calcula el estado del evento estilo Pokemon GO."""
        ahora = datetime.now()
        fecha_inicio_str = evento.get('Fecha_Inicio', '')
        fecha_termino_str = evento.get('Fecha_Termino', '')
        
        fecha_inicio = self._parsear_fecha(fecha_inicio_str)
        fecha_termino = self._parsear_fecha(fecha_termino_str)
        
        if not fecha_inicio or not fecha_termino:
            return {'tiempo_texto': 'Próximamente', 'color': (0.5, 0.5, 0.5, 1)}
        
        # Calcular diferencias de tiempo
        tiempo_hasta_inicio = fecha_inicio - ahora
        tiempo_desde_inicio = ahora - fecha_inicio
        tiempo_hasta_fin = fecha_termino - ahora
        tiempo_desde_fin = ahora - fecha_termino
        
        # CASO 1: Falta menos de 24 horas para que comience (cuenta regresiva)
        if tiempo_hasta_inicio.total_seconds() > 0 and tiempo_hasta_inicio.total_seconds() < 86400:  # 24 horas
            horas = int(tiempo_hasta_inicio.total_seconds() // 3600)
            minutos = int((tiempo_hasta_inicio.total_seconds() % 3600) // 60)
            return {
                'tiempo_texto': f'Inicia en {horas}h {minutos}m',
                'color': (0.2, 0.6, 1.0, 1)  # Azul
            }
        
        # CASO 2: Comenzó hace menos de 10 minutos
        elif tiempo_desde_inicio.total_seconds() >= 0 and tiempo_desde_inicio.total_seconds() < 600:  # 10 min
            minutos = int(tiempo_desde_inicio.total_seconds() // 60)
            return {
                'tiempo_texto': f'Iniciando evento ({minutos}m)',
                'color': (0.0, 0.8, 0.0, 1)  # Verde brillante
            }
        
        # CASO 3: Faltan menos de 10 minutos para terminar
        elif tiempo_hasta_fin.total_seconds() > 0 and tiempo_hasta_fin.total_seconds() < 600:  # 10 min
            minutos = int(tiempo_hasta_fin.total_seconds() // 60)
            return {
                'tiempo_texto': f'Terminando ({minutos}m)',
                'color': (1.0, 0.5, 0.0, 1)  # Naranja
            }
        
        # CASO 4: Evento en curso (entre 10 min de inicio y 10 min antes de terminar)
        elif tiempo_desde_inicio.total_seconds() >= 600 and tiempo_hasta_fin.total_seconds() >= 600:
            return {
                'tiempo_texto': 'Realizando evento',
                'color': (0.2, 0.6, 0.1, 1)  # Verde
            }
        
        # CASO 5: Terminó hace menos de 15 minutos
        elif tiempo_desde_fin.total_seconds() >= 0 and tiempo_desde_fin.total_seconds() < 900:  # 15 min
            minutos = int(tiempo_desde_fin.total_seconds() // 60)
            return {
                'tiempo_texto': f'Finalizado ({minutos}m)',
                'color': (0.6, 0.6, 0.6, 1)  # Gris
            }
        
        # CASO 6: Evento futuro (más de 24 horas)
        elif tiempo_hasta_inicio.total_seconds() > 86400:
            dias = int(tiempo_hasta_inicio.total_seconds() // 86400)
            return {
                'tiempo_texto': f'En {dias}d',
                'color': (0.4, 0.4, 0.8, 1)  # Azul oscuro
            }
        
        # Default
        return {'tiempo_texto': 'Próximamente', 'color': (0.5, 0.5, 0.5, 1)}
    
    def _actualizar_timers_eventos(self, dt):
        """Actualiza los contadores de tiempo de todos los eventos cada minuto."""
        try:
            for event_id, marker in self.marcadores_eventos.items():
                if event_id in self.eventos_data:
                    evento = self.eventos_data[event_id]
                    estado_info = self._calcular_estado_evento(evento)
                    marker.tiempo = estado_info['tiempo_texto']
            print(f"Timers de eventos actualizados: {len(self.marcadores_eventos)} eventos")
        except Exception as e:
            print(f"Error actualizando timers de eventos: {e}")

    def _abrir_detalle_evento(self, event_id, evento):
        """Abre el detalle de un evento (placeholder)."""
        print(f"Abriendo detalle del evento: {event_id}")
        print(f"Título: {evento.get('Titulo', 'Sin título')}")
    
    def aplicar_filtros(self):
        """Aplica los filtros seleccionados y recarga los eventos (SOLO MANUAL)."""
        try:
            # Obtener valores de los filtros
            if 'filtro_etiqueta' in self.ids:
                self.filtro_etiqueta_actual = self.ids.filtro_etiqueta.text
            else:
                self.filtro_etiqueta_actual = 'Todas'
                
            if 'filtro_mes' in self.ids:
                self.filtro_mes_actual = self.ids.filtro_mes.text
            else:
                self.filtro_mes_actual = 'Todos'
            
            print(f"\n=== APLICANDO FILTROS MANUALMENTE ===")
            print(f"Sector: {self.sector_actual}, Etiqueta: {self.filtro_etiqueta_actual}, Mes: {self.filtro_mes_actual}")
            
            # Limpiar marcadores actuales (excepto el del usuario)
            map_view = self.get_map_view()
            if map_view and hasattr(map_view, 'markers'):
                print(f"\n=== LIMPIANDO MARCADORES ===")
                print(f"Marcadores de eventos rastreados: {len(self.marcadores_eventos)}")
                print(f"Total marcadores en MapView antes: {len(map_view.markers)}")
                
                # Método 1: Eliminar usando el diccionario de rastreo
                for event_id, marker in list(self.marcadores_eventos.items()):
                    try:
                        if marker in map_view.markers:
                            map_view.remove_marker(marker)
                            print(f"  ✓ Marcador {event_id} eliminado")
                        else:
                            print(f"  ⚠ Marcador {event_id} no está en mapa")
                    except Exception as e:
                        print(f"  ✗ Error eliminando {event_id}: {e}")
                
                # Método 2: Eliminar marcadores de eventos que quedaron (por si acaso)
                for marker in list(map_view.markers):
                    # No eliminar el marcador del usuario
                    if marker != self.marker and hasattr(marker, 'event_id'):
                        try:
                            map_view.remove_marker(marker)
                            print(f"  ✓ Marcador huérfano eliminado: {getattr(marker, 'event_id', 'unknown')}")
                        except Exception as e:
                            print(f"  ✗ Error eliminando marcador huérfano: {e}")
                
                # Limpiar diccionarios
                self.marcadores_eventos.clear()
                self.eventos_data.clear()
                
                print(f"Total marcadores en MapView después: {len(map_view.markers)}")
                print(f"=== FIN LIMPIEZA ===\n")
            else:
                print("No se pudo acceder al MapView o no tiene atributo 'markers'")
            
            # Recargar eventos con nuevos filtros
            self.cargar_eventos()
            
        except Exception as e:
            print(f"Error aplicando filtros: {e}")
            import traceback
            traceback.print_exc()
    
    def buscar_sector_manual(self):
        """Busca una ubicación manualmente y cambia el sector para ver eventos de ese lugar."""
        try:
            if 'buscar_ubicacion' not in self.ids:
                return
            
            ubicacion_texto = self.ids.buscar_ubicacion.text.strip()
            if not ubicacion_texto:
                print("No se ingresó ninguna ubicación")
                return
            
            print(f"Buscando ubicación: {ubicacion_texto}")
            
            # Usar Nominatim para geocodificar la dirección
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="buzzevent_map")
            
            # Buscar la ubicación
            location = geolocator.geocode(ubicacion_texto, language='es')
            
            if location:
                lat = location.latitude
                lon = location.longitude
                
                print(f"Ubicación encontrada: {lat}, {lon}")
                
                # Obtener el sector de esas coordenadas (geocodificación inversa)
                location_reverse = geolocator.reverse((lat, lon), language='es')
                
                if location_reverse and 'address' in location_reverse.raw:
                    direccion = location_reverse.raw['address']
                    country = direccion.get('country', 'Unknown')
                    state = direccion.get('state', 'Unknown')
                    county = direccion.get('county', 'Unknown')
                    city = direccion.get('city', 'Unknown')
                    
                    # Actualizar sector
                    self.sector_actual = f"{country}_{state}_{county}_{city}"
                    
                    # Actualizar label
                    if 'label_sector' in self.ids:
                        ciudad = direccion.get('city', direccion.get('town', direccion.get('village', ubicacion_texto)))
                        self.ids.label_sector.text = f'Sector: {ciudad}'
                    
                    print(f"Sector cambiado a: {self.sector_actual}")
                    
                    # Centrar mapa en la nueva ubicación
                    map_view = self.get_map_view()
                    if map_view:
                        map_view.center_on(lat, lon)
                        map_view.zoom = 13
                    
                    # Aplicar filtros con el nuevo sector
                    self.aplicar_filtros()
                    
                    # Limpiar el campo de búsqueda
                    self.ids.buscar_ubicacion.text = ''
                else:
                    print("No se pudo obtener información del sector")
                    if 'label_sector' in self.ids:
                        self.ids.label_sector.text = 'Sector: No encontrado'
            else:
                print(f"No se encontró la ubicación: {ubicacion_texto}")
                if 'label_sector' in self.ids:
                    self.ids.label_sector.text = 'Sector: No encontrado'
                    
        except Exception as e:
            print(f"Error buscando ubicación: {e}")
            import traceback
            traceback.print_exc()
            if 'label_sector' in self.ids:
                self.ids.label_sector.text = 'Sector: Error en búsqueda'
    
    def toggle_filters(self):
        """Alterna la visibilidad de los filtros."""
        self.show_filters = not self.show_filters
        print(f"Filtros {'mostrados' if self.show_filters else 'ocultados'}")
    
    def _aplicar_filtros_eventos(self, eventos):
        """Filtra eventos según sector, etiqueta y mes."""
        eventos_filtrados = {}
        
        meses_dict = {
            'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
            'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
            'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
        }
        
        print(f"\n=== FILTRANDO EVENTOS ===")
        print(f"Sector usuario: '{self.sector_actual}'")
        print(f"Etiqueta: '{self.filtro_etiqueta_actual}'")
        print(f"Mes: '{self.filtro_mes_actual}'")
        print(f"Total eventos a filtrar: {len(eventos)}\n")
        
        for event_id, evento in eventos.items():
            titulo = evento.get('Titulo', 'Sin título')
            
            # FILTRO OBLIGATORIO: Sector
            ubicacion = evento.get('Ubicacion', {})
            if not isinstance(ubicacion, dict):
                print(f"❌ '{titulo}': Ubicación no es diccionario")
                continue
            
            sector_evento = ubicacion.get('Sector', '')
            
            # DEBUG: Mostrar ubicación completa si no hay sector
            if not sector_evento or sector_evento.strip() == '':
                print(f"⚠️  '{titulo}': Sin sector en Ubicacion")
                print(f"     Ubicacion completa: {ubicacion}")
                print(f"     Event ID: {event_id}")
                # SOLUCIÓN: Extraer sector del event_id si es posible
                # El event_id puede contener el sector en la estructura de Firebase
                # Por ahora, saltamos eventos sin sector
                continue
            
            # Si el usuario no tiene sector definido, mostrar todos los eventos con sector
            if not self.sector_actual:
                print(f"⚠️  '{titulo}': Usuario sin sector - evento permitido")
            # Si ambos tienen sector, deben coincidir
            elif sector_evento != self.sector_actual:
                print(f"❌ '{titulo}': Sector '{sector_evento}' != '{self.sector_actual}'")
                continue
            else:
                print(f"✅ '{titulo}': Sector coincide")
            
            # FILTRO OPCIONAL: Etiqueta
            if self.filtro_etiqueta_actual != 'Todas':
                etiquetas = evento.get('Etiquetas', [])
                if self.filtro_etiqueta_actual not in etiquetas:
                    print(f"  ❌ Filtrado por etiqueta: {etiquetas}")
                    continue
                print(f"  ✅ Etiqueta coincide")
            
            # FILTRO OPCIONAL: Mes
            if self.filtro_mes_actual != 'Todos':
                fecha_inicio_str = evento.get('Fecha_Inicio', '')
                fecha_inicio = self._parsear_fecha(fecha_inicio_str)
                
                if fecha_inicio:
                    mes_evento = fecha_inicio.month
                    mes_filtro = meses_dict.get(self.filtro_mes_actual)
                    
                    if mes_filtro and mes_evento != mes_filtro:
                        print(f"  ❌ Filtrado por mes: {mes_evento} != {mes_filtro}")
                        continue
                    print(f"  ✅ Mes coincide")
            
            # Si pasó todos los filtros, agregarlo
            print(f"✓ '{titulo}' AGREGADO\n")
            eventos_filtrados[event_id] = evento
        
        print(f"=== RESULTADO: {len(eventos_filtrados)} eventos de {len(eventos)} ===\n")
        return eventos_filtrados

    # --- NAVEGACIÓN ---

    def Regresar_Estandar(self):
        """Regresa a la pantalla correspondiente según el rol."""
        for widget in Window.children[:]:
            if isinstance(widget, (Menu_Evento_Base, ModalView)):
                try: widget.dismiss()
                except Exception: pass
        
        rol = Singleton_Perfil.get_instance().tipo_perfil
        if rol == 'Estandar':
            self.abrir_otra_pantalla("BA_Estandar", transition=SlideTransition(direction="right"))
        elif rol == 'Organizador':
            self.abrir_otra_pantalla("BB_Organizador", transition=SlideTransition(direction="right"))
        elif rol == 'Administrador':
            self.abrir_otra_pantalla("BC_Administrador", transition=SlideTransition(direction="right"))
        else:
            self.abrir_otra_pantalla("AA_Login", transition=SlideTransition(direction="right"))

    def actualizar_mapa_a_ubicacion(self):
        """Obtiene la instancia del MapView y le asigna las coordenadas actuales."""
        map_view = self.get_map_view()
        if map_view:
            map_view.lat = self.latitud
            map_view.lon = self.longitud
            print(f"Mapa actualizado a Lat: {self.latitud}, Lon: {self.longitud}")
        else:
            print("No se puede actualizar el mapa: MapView no encontrado.")
        
        Clock.schedule_once(self._mover_mapa_al_centro, 0)

    def on_location_updated(self, lat, lon):
        """Callback cuando la ubicación se actualiza."""
        self.ubicacion_actualizada = True
        self.actualizar_mapa_a_ubicacion()
        
    def _mover_mapa_al_centro(self, dt):
        """Función interna para ser llamada por el Clock."""
        map_view = self.get_map_view()
        
        if map_view:
            map_view.center_on(self.latitud, self.longitud)
            map_view.zoom = self.zoom
            print(f"Mapa MOVIDO a Lat: {self.latitud}, Lon: {self.longitud}")
