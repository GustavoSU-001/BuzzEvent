import os
import shutil
import logging
from functools import partial
from pathlib import Path

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

# --- GARDEN / EXTERNAL IMPORTS ---
from kivy_garden.mapview import MapView, MapMarkerPopup
# Intentar importar plyer.gps solo si es necesario (asumo que se debe instalar o comentar)
try:
    from plyer import gps
except ImportError:
    gps = None
    
# --- CONFIGURACIÓN GLOBAL ---
# Configurar logging (Mejor hacerlo una vez y al inicio del módulo)
# Desactivar loggers ruidosos
LOG_LEVEL_KIVY = logging.WARNING
LOG_LEVEL_URL = logging.WARNING

logging.getLogger('urllib3.connectionpool').setLevel(LOG_LEVEL_URL)
logging.getLogger('kivy').setLevel(LOG_LEVEL_KIVY)
os.environ['KIVY_NO_FILELOG'] = '1'
os.environ['KIVY_NO_CONSOLELOG'] = '1'
# Configuraciones adicionales se pueden hacer en un método estático como antes, si se requiere una lógica más fina.


# --- CLASES DE WIDGETS ---
class ElementoEstrella(Widget):
    # 1. Propiedades con valor inicial numérico para evitar el NoneType
    t = NumericProperty(50.0) 
    r = NumericProperty(20.0) 
    porcentaje_visible = NumericProperty(0.5)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 2. Programamos el cálculo de tamaño para que ocurra después de que el widget se ha inicializado
        # Esto es más seguro que solo usar on_size directamente.
        self.bind(size=self._actualizar_radios) 
        
    def _actualizar_radios(self, instance, value):
        # Aseguramos que el cálculo solo se haga si el tamaño es válido
        if self.width > 0 and self.height > 0:
            self.t = min(self.width, self.height) * 0.45
            self.r = self.t * 0.4
    
    def calificar(self, evento_id, calificacion):
        pass

class Menu_Evento_Informacion(BoxLayout):
    # Define las propiedades que estás pasando en el constructor:
    descrip = StringProperty('')  # Para cadenas de texto
    calificacion = NumericProperty(0)


# La clase Menu_Evento DEBERÍA estar en un archivo KV o en un módulo separado
class Menu_Evento(ModalView):
    """Popup modal para mostrar detalles de un evento."""
    titulo = StringProperty('')
    def Limpiar_contenido(self):
        self.ids.listado_menu_evento.clear_widgets()
        
    def Cargar_Interfaz_Imagenes(self):
        self.ids.listado_menu_evento.clear_widgets()
        elementos=[]
        for e in elementos:
            imagen=Factory.Menu_Evento_Imagen(imagen=e['imagen'])
            self.ids.listado_menu_evento.add_widgets(imagen)

        
    def Cargar_Interfaz_Informacion(self):
        self.ids.listado_menu_evento.clear_widgets()
        elementos={
            'descripcion': 'Este es un ejemplo de descripción. Lorem ipsum dolor sit amet consectetur adipiscing elit justo, suscipit congue lectus pellentesque vulputate imperdiet feugiat, est ligula augue nibh litora egestas torquent. Lobortis tellus integer potenti ornare commodo duis platea accumsan sed proin, leo mauris iaculis et mollis metus consequat orci ullamcorper, sapien euismod venenatis eros dapibus arcu cubilia facilisi posuere. Metus mauris porttitor pharetra hendrerit dis interdum netus, sociis aliquam nulla leo tincidunt himenaeos semper, tellus suspendisse venenatis etiam integer proin.',
            'ubicacion': 'Lomas Turbas #145, Los Angeles, Bio bio, Chile',
            'calificacion': 3.3,
            'etiquetas':["Etiqueta1","Etiqueta2","Etiqueta3","Etiqueta4"]
        }
        interfaz = Factory.Menu_Evento_Informacion()
        interfaz.texto=elementos['descripcion']
        interfaz.calificacion=elementos["calificacion"]
        interfaz.ubicacion=elementos["ubicacion"]
        
        for e in elementos["etiquetas"]:
            etiqueta=Factory.Etiqueta_Evento()
            etiqueta.texto=e
            etiqueta.altura=50
            interfaz.ids.lista_etiquetas.add_widget(etiqueta)
        
        rol=Singleton_Perfil.get_instance().tipo_perfil
        if rol == "Organizador":
            etiqueta=Factory.Etiqueta_Evento()
            etiqueta.texto='+'
            etiqueta.altura=50
            interfaz.ids.lista_etiquetas.add_widget(etiqueta)
        
        self.ids.listado_menu_evento.add_widget(interfaz)
        
            
        
    def Cargar_Interfaz_ListaCompras(self):
        self.ids.listado_menu_evento.clear_widgets()
        Shop=Factory.Menu_Evento_ListaCompra()
        self.ids.listado_menu_evento.add_widget(Shop)
    
    def Cargar_Interfaz_Comprando(self):
        pass
        
    def Cargar_Interfaz_Reporte(self):
        pass

class Miniatura_Evento(MapMarkerPopup):
    """
    Clase que extiende MapMarkerPopup para incluir propiedades personalizadas
    usadas en el popup.
    """
    # 💥 PROPIEDADES CRÍTICAS FALTANTES 💥
    title = StringProperty('Título de Evento')
    tiempo = StringProperty("15d")
    action = ObjectProperty(None, allownone=True)
    # Nota: No olvides importar StringProperty y ObjectProperty de kivy.properties
    
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
    
   # Referencias a los relojes: NECESITAN allownone=True
    _reloj_inicio = ObjectProperty(None, allownone=True)
    _reloj_cache = ObjectProperty(None, allownone=True)
    _gps_timeout_ev = ObjectProperty(None, allownone=True)
    marker = ObjectProperty(None, allownone=True) # Si marker también puede ser None

    # --- INICIALIZACIÓN ---
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super().__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        # Referencias para evitar errores al cancelar
        self._reloj_inicio = None
        self._reloj_cache = None
        self._gps_timeout_ev = None
        
    def get_map_view(self):
        """
        Busca la instancia de MapView dentro del contenedor 'mapa'.
        Es robusto para widgets añadidos dinámicamente.
        """
        map_container = self.ids.get('mapa') 
        
        if map_container and map_container.children:
            from kivy_garden.mapview import MapView
            # Recorre todos los hijos y devuelve el primero que sea un MapView
            for child in map_container.children:
                if isinstance(child, MapView): 
                    return child
        
        # print("No se encontró map_view.") # Comenta esto para reducir ruido
        return None

    # --- CICLO DE VIDA ---

    def Iniciar_Ventana(self):
        print("Iniciando Layout_Mapa...")
    
        # 1. Limpia y REMUEVE la instancia anterior
        self.limpiar_mapa_profundamente() 
        
        # 2. CREAR Y AÑADIR LA NUEVA INSTANCIA DE MAPVIEW
        map_container = self.ids.get('mapa')
        if not map_container:
            print("ERROR: Contenedor 'mapa' (id) no encontrado en el layout.")
            return

        # CORRECCIÓN: Pasamos las propiedades lat, lon, zoom directamente
        new_map_view = Factory.AgregarMapa(
            lat=self.latitud,      # Toma el valor actual de Layout_Mapa
            lon=self.longitud,     # Toma el valor actual de Layout_Mapa
            zoom=self.zoom         # Toma el valor actual de Layout_Mapa
        )
        
        # Agregamos el MapView al contenedor.
        # A partir de este momento, new_map_view.parent ya no es None.
        
        map_container.add_widget(new_map_view)
        print("Nueva instancia de MapView añadida y lista.")

        # 3. INICIALIZAR LÓGICA (timers, etc.)
        self.buscar_y_limpiar_cache() 
        
        self._reloj_inicio = Clock.schedule_once(self._initialize_location_task, 2)
        self._reloj_cache = Clock.schedule_interval(self.limpiar_cache, 5)
        
        print("Layout_Mapa inicializado")
        #self.Agregar_Marcador(-36.8336, -73.04898, "Lugarcito", lambda *args: print("Se presionó el marcador"))

    def stop_gps(self):
        """Detiene la escucha del GPS y cancela el timeout."""
        
        # 1. Cancelar Clock de timeout (Esto es seguro en cualquier plataforma)
        if self._gps_timeout_ev:
            try: self._gps_timeout_ev.cancel()
            except Exception: pass
            self._gps_timeout_ev = None
            
        # 2. 💥 CORRECCIÓN CRÍTICA: Solo intentar detener el servicio GPS si estamos en Android 💥
        if platform == "android":
            if gps:
                try: 
                    gps.stop()
                    print("Servicio GPS detenido en Android.")
                except Exception as e: 
                    # Este catch evitaría errores si hay problemas con la implementación de Plyer
                    print(f"Error al detener GPS en Android: {e}")
    
    def Cerrar_Ventana(self):
        """Limpia todos los recursos al salir de la pantalla."""
        print("Cerrando Layout_Mapa...")
        self.stop_gps()
        self.limpiar_mapa_profundamente()
        
        # El widget debe ser limpiado por el ScreenManager o el contenedor
        # self.ids.mapa.clear_widgets() # Esto ya no es necesario si se usa el ScreenManager
        # o si se llama a este método antes de remover el widget.

    # --- LIMPIEZA PROFUNDA (Consolidado) ---
    def limpiar_mapa_profundamente(self):
        """
        Limpia completamente el MapView y lo remueve del layout de forma segura.
        """
        map_view = self.get_map_view()

        # 1. Cancelar Clocks
        if self._reloj_inicio:
            self._reloj_inicio.cancel()
        if self._reloj_cache:
            self._reloj_cache.cancel()
            
        # 2. LIMPIEZA Y REMOCIÓN DEL WIDGET
        if map_view:
            
            # Detiene la descarga de tiles (CRÍTICO)
            if hasattr(map_view, 'stop_downloading'):
                map_view.stop_downloading() 
            
            # Pausa el procesamiento de eventos internos
            map_view._pause = True 
            
            # Limpieza de marcadores
            if hasattr(map_view, 'markers'):
                for marker in list(map_view.markers):
                    map_view.remove_marker(marker)
            
            # Paso CRÍTICO: Remover la instancia del MapView de su padre
            if map_view.parent:
                map_view.parent.remove_widget(map_view)
            
            print("MapView retirado del layout.")

    # --- MARCADORES ---

    def Agregar_Marcador(self, lat, lon, title="Lugar", callback=None, source_img=None):
        """Agrega un MapMarker al mapa."""
        map_view = self.get_map_view()
        if not map_view:
            print("No se encontró map_view.")
            return None
        
        try:
            # Usamos Factory para instanciar la clase definida en KV (Miniatura_Evento)
            marker = Factory.Miniatura_Evento(
                lat=lat, 
                lon=lon, 
                title=title, 
                marker_source=source_img if source_img else 'atlas://map_icons/pin'
            )
            
            if callback:
                # El callback se asigna al atributo 'action' del marcador si lo tiene
                marker.action = callback 
            
            map_view.add_marker(marker)
            return marker
            
        except Exception as e:
            print(f"Error al agregar marcador: {e}")
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
        
    # La función Eliminar_todos_marcadores se reemplaza por limpiar_mapa_profundamente

    # --- GESTIÓN DE CACHÉ ---
    
    def buscar_y_limpiar_cache(self):
        """
        Limpia de forma segura los archivos de caché de MapView 
        (solo custom_map_) y limita el número de archivos.
        """
        try:
            # NO ELIMINAR EL DIRECTORIO '.cache' de Kivy.
            # Solo gestionamos la caché de MapView en el directorio 'cache'.
            
            cache_dir = Path(os.getcwd()) / 'cache'
            
            if cache_dir.exists():
                cache_files = []
                # Solo buscamos archivos de mapa personalizados
                for file_path in cache_dir.glob('custom_map_*'):
                    # Guardamos el tiempo de modificación y la ruta
                    cache_files.append((file_path.stat().st_mtime, file_path))
                
                # Ordenar de más nuevo a más antiguo
                cache_files.sort(key=lambda x: x[0], reverse=True)
                
                # Eliminar todos excepto los 12 más recientes
                for _, file_path in cache_files[12:]: 
                    try:
                        file_path.unlink() # Eliminar el archivo
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
        """Decide si usar GPS (Android) o IP (PC). Ahora inicia escucha continua en Android."""
        if platform == "android" and gps:
            self.request_android_permissions()
            try:
                # 💥 Iniciamos la escucha continua 💥
                gps.configure(on_location=self._on_location, on_status=self._on_status)
                # minTime > 1000ms o minDistance > 0m asegura actualizaciones más frecuentes
                gps.start(minTime=1000, minDistance=5) 
                
                # Mantenemos el timeout por si nunca logra encontrar una ubicación inicial
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
        
        # Usamos partial para simplificar la definición de callbacks
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
        
        # 1. Cancelar GPS Timeout si la ubicación es válida (¡Esto es vital!)
        if self._gps_timeout_ev:
            try: self._gps_timeout_ev.cancel()
            except Exception: pass

        # ** NO LLAMAR gps.stop() AQUÍ **
            
        try:
            lat = float(kwargs.get('lat', self.LAT_DEFAULT))
            lon = float(kwargs.get('lon', self.LON_DEFAULT))
            
            if lat and lon:
                self.latitud = lat
                self.longitud = lon
                self.zoom = 15 # Puedes mantener un zoom constante
                self.ubicacion_actualizada = True
                
                # 💥 PASO CRÍTICO: Mover el mapa y el marcador 💥
                self.mover_marcador_usuario(lat, lon) 
                
                print(f"Ubicación actualizada: {lat}, {lon}")
                                
        except Exception as e:
            print(f"Error en _on_location: {e}")

    def mover_marcador_usuario(self, lat, lon):
        """Mueve el marcador de usuario y centra el mapa en él."""
        map_view = self.get_map_view()
        
        if map_view:
            # Si el marcador ya existe, simplemente actualiza su posición
            if self.marker:
                self.marker.lat = lat
                self.marker.lon = lon
            else:
                # Si es la primera vez (por el timeout o el inicio), créalo.
                # Asegúrate de usar la imagen del círculo aquí también
                self.marker = self.Agregar_Marcador(
                    lat=lat, 
                    lon=lon, 
                    title="Ubicación Actual",
                    callback=lambda *args: print("Usuario presionado"),
                    source_img='Static\\Imagenes\\circulo_usuario.png' 
                )
            
            # Opcional: Centrar el mapa en la nueva ubicación
            map_view.center_on(lat, lon)
        else:
            # Si el mapa aún no está cargado, simplemente actualiza las propiedades
            self.latitud = lat
            self.longitud = lon


    def _on_status(self, stype, status):
        """Maneja el estado del GPS (opcional)."""
        pass

    # --- NAVEGACIÓN ---

    def Regresar_Estandar(self):
        """Regresa a la pantalla BA_Estandar."""
        # Cerrar popups restantes antes de la transición
        for widget in Window.children[:]:
            if isinstance(widget, (Menu_Evento, ModalView)):
                try: widget.dismiss()
                except Exception: pass
        
        # Asumo que self.abrir_otra_pantalla está definido en el Screen y llama al Manager
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
        """
        Obtiene la instancia del MapView y le asigna las coordenadas
        actuales del Layout_Mapa.
        """
        map_view = self.get_map_view()
        if map_view:
            # Forzar la actualización del centro del mapa
            map_view.lat = self.latitud
            map_view.lon = self.longitud
            print(f"Mapa actualizado a Lat: {self.latitud}, Lon: {self.longitud}")
        else:
            print("No se puede actualizar el mapa: MapView no encontrado.")
        
        Clock.schedule_once(self._mover_mapa_al_centro, 0)


    # Modifica el método que recibe la ubicación (ejemplo: on_location_updated)
    def on_location_updated(self, lat, lon):
        # Esto ya lo debes estar haciendo:
        #self.latitud = lat
        #self.longitud = lon
        self.ubicacion_actualizada = True # Asumiendo que usas esta bandera
        
        # 💥 PASO CRÍTICO: LLAMAR A LA FUNCIÓN DE ACTUALIZACIÓN
        # 💥 PASO CLAVE: Mover el mapa a la nueva ubicación
        self.actualizar_mapa_a_ubicacion()
        
    def _mover_mapa_al_centro(self, dt):
        """Función interna para ser llamada por el Clock."""
        map_view = self.get_map_view()
        
        if map_view:
            # 1. Mover el mapa al centro inicial (IP o DEFAULT)
            map_view.center_on(self.latitud, self.longitud)
            map_view.zoom = self.zoom
            
            print(f"Mapa MOVIDO a Lat: {self.latitud}, Lon: {self.longitud}")
            
            # 2. 💥 ELIMINAR O COMENTAR LA CREACIÓN DEL MARCADOR 💥
            # La función mover_marcador_usuario se encarga de esto en el callback
            
        else:
            print("No se pudo mover el mapa: MapView no encontrado.")
        
        
        
  