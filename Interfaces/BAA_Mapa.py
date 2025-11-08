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
        self.Agregar_Marcador(-36.8336, -73.04898, "Lugarcito", lambda *args: print("Se presionó el marcador"))

    def Cerrar_Ventana(self):
        """Limpia todos los recursos al salir de la pantalla."""
        print("Cerrando Layout_Mapa...")
        self.limpiar_mapa_profundamente()
        
        # El widget debe ser limpiado por el ScreenManager o el contenedor
        # self.ids.mapa.clear_widgets() # Esto ya no es necesario si se usa el ScreenManager
        # o si se llama a este método antes de remover el widget.

    # --- LIMPIEZA PROFUNDA (Consolidado) ---
    def limpiar_mapa_profundamente(self):
        """
        Limpia completamente el MapView y lo remueve del layout.
        """
        map_view = self.get_map_view()

        # 1. Cancelar Clocks (Esto ya lo corregiste)
        # ...
        Clock.unschedule(self.limpiar_cache)


        # 2. 💥 LIMPIEZA Y REMOCIÓN DEL WIDGET
        if map_view:
            # 2a. Limpieza de recursos MapView
            if hasattr(map_view, 'markers'):
                for marker in list(map_view.markers):
                    map_view.remove_marker(marker)
            
            # --- CORRECCIÓN CRÍTICA ---
            # Reemplazar map_view.stop_animation() por funciones válidas:
            
            # Detiene la descarga de tiles (recomendado al salir)
            if hasattr(map_view, 'stop_downloading'):
                    map_view.stop_downloading() 
            
            # Pausa el procesamiento de eventos internos
            map_view._pause = True 
            
            # 2b. PASO CRÍTICO: Remover la instancia del MapView de su padre
            if map_view.parent:
                map_view.parent.remove_widget(map_view)
            
            print("MapView retirado del layout.")

        # 3. Limpieza de archivos de caché
        self.buscar_y_limpiar_cache()
        print("Limpieza profunda completada.")

    # --- MARCADORES ---

    def Agregar_Marcador(self, lat, lon, title="Lugar", callback=None):
        """Agrega un MapMarker al mapa."""
        map_view = self.get_map_view()
        if not map_view:
            print("No se encontró map_view.")
            return None
        
        try:
            # Usamos Factory para instanciar la clase definida en KV (Miniatura_Evento)
            marker = Factory.Miniatura_Evento(lat=lat, lon=lon, title=title)
            
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
        """Limpia directorios de caché externos (.cache, cache) y limita archivos."""
        try:
            # Limpiar .cache (completo)
            dot_cache_dir = Path(os.getcwd()) / '.cache'
            if dot_cache_dir.exists():
                shutil.rmtree(dot_cache_dir)

            # Gestionar caché de MapView (solo custom_map_)
            cache_dir = Path(os.getcwd()) / 'cache'
            if cache_dir.exists():
                cache_files = []
                for file_path in cache_dir.glob('custom_map_*'):
                    cache_files.append((file_path.stat().st_mtime, file_path))
                
                cache_files.sort(key=lambda x: x[0], reverse=True)
                
                # Eliminar todos excepto los 12 más recientes (ajustado de 4 a 12 para mayor seguridad)
                for _, file_path in cache_files[12:]: 
                    try:
                        file_path.unlink() # Eliminar el archivo
                    except Exception:
                        pass
            return True
        except Exception as e:
            print(f"Error durante la gestión del caché: {e}")
            return False

    def limpiar_cache(self, dt):
        """Tarea programada para limpiar el caché periódicamente."""
        self.buscar_y_limpiar_cache()
        map_view = self.get_map_view()
        
        if map_view:
            # Limpiar caché interno del MapView
            if hasattr(map_view, '_tiles'):
                map_view._tiles.clear()
            if hasattr(map_view, 'map_source') and hasattr(map_view.map_source, 'cache'):
                map_view.map_source.cache = {}
            
            # Forzar re-renderizado
            map_view.zoom = map_view.zoom
            Window.canvas.ask_update()
            
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
                gps.start(minTime=1000, minDistance=0)
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
        
        # 1. Cancelar GPS Timeout y Detener GPS
        if self._gps_timeout_ev:
            try: self._gps_timeout_ev.cancel()
            except Exception: pass

        if gps:
            try: gps.stop()
            except Exception: pass
            
        try:
            # 2. Obtener Coordenadas y asegurar que sean float
            lat = float(kwargs.get('lat', self.LAT_DEFAULT))
            lon = float(kwargs.get('lon', self.LON_DEFAULT))
            
            # 3. Solo actualiza si los valores son válidos
            if lat and lon:
                # 4. Establecer las propiedades de la clase (Latitud/Longitud)
                self.latitud = lat
                self.longitud = lon
                self.zoom = 15
                self.ubicacion_actualizada = True
                
                # 5. 💥 PASO CLAVE: LLAMAR A LA FUNCIÓN DE ACTUALIZACIÓN
                #    Usamos 'lat' y 'lon' (las coordenadas locales)
                self.on_location_updated(lat, lon) 
                
                # 6. Mensajes de consola
                if 'city' in kwargs and kwargs['city']:
                    print(f"Ubicación por IP: {kwargs['city']}, {kwargs.get('country')}")
                else:
                    print(f"Ubicación actualizada: {lat}, {lon}")
                    
        except ValueError:
            print("Advertencia: Coordenadas no válidas.")
        except Exception as e:
            print(f"Error en _on_location: {e}")

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
        self.abrir_otra_pantalla("BA_Estandar", transition=SlideTransition(direction="right"))

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
            # 1. Mover el mapa
            map_view.center_on(self.latitud, self.longitud)
            map_view.zoom = self.zoom
            print(f"Mapa MOVIDO a Lat: {self.latitud}, Lon: {self.longitud}")
            
            # 2. 💥 CREAR/ACTUALIZAR MARCADOR DE UBICACIÓN ACTUAL
            # Si ya existe un marcador para la ubicación actual (self.marker), lo eliminamos
            if self.marker:
                self.Eliminar_marcador(self.marker) # Usamos tu función de eliminación
            
            # Creamos y guardamos el nuevo marcador usando la función que ya usa Miniatura_Evento
            # Asignamos el resultado a self.marker (la propiedad de la clase)
            self.marker = self.Agregar_Marcador(
                lat=self.latitud, 
                lon=self.longitud, 
                title="Ubicación Actual",
                callback=lambda *args: print("Marcador de ubicación actual presionado")
            )
            
        else:
            print("No se pudo mover el mapa: MapView no encontrado.")   
        
        
        
        

# from kivy.uix.floatlayout import FloatLayout
# from kivy.uix.screenmanager import SlideTransition
# from kivy_garden.mapview import MapView, MapMarker
# from kivy.utils import platform
# from kivy.uix.modalview import ModalView
# from kivy.properties import StringProperty
# from kivy.core.window import Window
# #from plyer import gps
# from kivy.clock import Clock
# import urllib.request
# import json
# import socket
# import os
# import logging
# import shutil
# from kivy.network.urlrequest import UrlRequest
# from pathlib import Path
# from functools import partial

# from kivy.factory import Factory

# # Definición de la clase Menu_Evento
# class Menu_Evento(ModalView):
#     titulo = StringProperty('')
   

# # Configurar logging
# logging.getLogger('urllib3').setLevel(logging.WARNING)
# logging.getLogger('kivy').setLevel(logging.WARNING)
# os.environ['KIVY_NO_FILELOG'] = '1'  # Desactivar logging a archivo
# os.environ['KIVY_NO_CONSOLELOG'] = '1'  # Desactivar logging a consola




# from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
# from kivy.core.window import Window

# class Layout_Mapa(FloatLayout):
#     latitud = NumericProperty(-33.4569400)  # Santiago por defecto
#     longitud = NumericProperty(-70.6482700)
#     zoom = NumericProperty(12)
#     marker = ObjectProperty(None)
#     ubicacion_actualizada = BooleanProperty(False)  # Para controlar cuando actualizar el marcador
#     def __init__(self, abrir_otra_pantalla, **kwargs):
#         super(Layout_Mapa,self).__init__(**kwargs)
#         self.abrir_otra_pantalla=abrir_otra_pantalla
        
#     def Iniciar_Ventana(self):
#         print("Iniciando Layout_Mapa...")
        
#         # Asegurarse de que no haya caché al inicio
#         self.buscar_y_limpiar_cache()
        
#         # Configurar logging antes de inicializar
#         self.configure_logging()
        
#         # Obtener ubicación después de que el widget esté listo
#         self.reloj=Clock.schedule_once(self._initialize_location, 2)
        
#         # Programar limpieza periódica del caché
#         self.relojito=Clock.schedule_interval(self.limpiar_cache, 5)  # Cada 5 segundos
        
#         print("Layout_Mapa inicializado")
#         self.Agregar_Marcador(-36.8336, -73.04898, "Lugarcito",print("Se Preciono el marcador"))
        
#     def Cerrar_Ventana(self):
#         try:
#             # Detener cualquier animación del mapa
#             if hasattr(self, 'ids') and 'map_view' in self.ids:
#                 map_view = self.ids.map_view
#                 # Detener todas las animaciones del MapView
#                 if hasattr(map_view, '_scale_anim'):
#                     map_view._scale_anim.stop(map_view)
#                 if hasattr(map_view, '_scatter'):
#                     map_view._scatter.transform_with_touch = lambda touch: None
            
#             # Cancelar todos los eventos programados primero
#             Clock.unschedule(self._initialize_location)
#             Clock.unschedule(self.limpiar_cache)
            
#             # Cancelar relojes específicos
#             if hasattr(self, 'reloj') and self.reloj:
#                 try:
#                     self.reloj.cancel()
#                     self.reloj = None
#                 except Exception:
#                     pass
                    
#             if hasattr(self, 'relojito') and self.relojito:
#                 try:
#                     self.relojito.cancel()
#                     self.relojito = None
#                 except Exception:
#                     pass
            
#             # Eliminar marcadores y popups
#             self.Eliminar_todos_marcadores()
            
#             # Cerrar popups restantes
#             for widget in Window.children[:]:
#                 if isinstance(widget, (Menu_Evento, ModalView)):
#                     try:
#                         widget.dismiss()
#                     except Exception:
#                         pass
            
#             # Limpiar referencias del mapa de manera segura
#             if hasattr(self, 'ids') and 'map_view' in self.ids:
#                 map_view = self.ids.map_view
#                 try:
#                     # Detener la actualización del mapa
#                     map_view._pause = True
#                     # Limpiar los tiles
#                     if hasattr(map_view, '_tiles'):
#                         map_view._tiles.clear()
#                     # Desconectar eventos
#                     map_view.unbind_all()
#                 except Exception:
#                     pass
                    
#         except Exception as e:
#             print(f"Error al cerrar ventana: {e}")
            
#         finally:
#             # Asegurarse de que todas las referencias estén limpias
#             if hasattr(self, 'ids') and 'map_view' in self.ids:
#                 self.ids.map_view._pause = True
            
#         self.ids.mapa.clear_widgets()
        
        
    
#     def Regresar_Estandar(self):
#         # Cerrar todos los popups abiertos antes de cambiar de pantalla
#         for widget in Window.children[:]:
#             if isinstance(widget, (Menu_Evento, ModalView)):
#                 widget.dismiss()
#         self.abrir_otra_pantalla("BA_Estandar", transition= SlideTransition(direction="right"))
    
#     def Agregar_Marcador(self, lat, lon, title="Lugar", callback=None):
#         try:
#             print(f"Intentando agregar marcador en lat:{lat}, lon:{lon}")
            
#             # Crear el marcador popup con el menú de evento
#             marker = Factory.Miniatura_Evento()
#             marker.lat = lat
#             marker.lon = lon
#             marker.title = title
            
#             if callback:
#                 marker.action = callback
            
#             # Obtener el mapa y agregar el marcador
#             map_view = self.ids.get('map_view')
#             if not map_view:
#                 print("No se encontró map_view en ids")
#                 return None
            
#             map_view.add_marker(marker)
#             print(f"Marcador agregado exitosamente en {lat}, {lon}")
#             return marker
            
#         except Exception as e:
#             print(f"Error al agregar marcador: {e}")
        
#     def Eliminar_marcador(self, marker):
#         """Elimina un marcador específico del mapa"""
#         try:
#             map_view = self.ids.get('map_view')
#             if map_view and marker:
#                 map_view.remove_marker(marker)
#                 print(f"Marcador eliminado: {marker}")
#                 return True
#         except Exception as e:
#             print(f"Error al eliminar marcador: {e}")
#         return False

#     def Eliminar_todos_marcadores(self):
#         print("Eliminando todos los marcadores...")
        
#         if not hasattr(self, 'ids') or 'map_view' not in self.ids:
#             print("ERROR: La referencia 'map_view' en self.ids no está disponible.")
#             # Podrías agregar un Clock.schedule_once para reintentar si es necesario.
#             return
            
#         map_view = self.ids.map_view
        
#         # 💡 Doble verificación: Asegúrate de que MapView haya inicializado su lista 'markers'
#         if not hasattr(map_view, 'markers'):
#             print("ERROR: MapView aún no ha inicializado su atributo 'markers'.")
#             return

#         # El código a continuación es correcto, ya que markers ahora existe:
        
#         # Copiar la lista antes de iterar para evitar errores de cambio de tamaño
#         markers_to_remove = list(map_view.markers) 
        
#         for marker in markers_to_remove:
#             map_view.remove_marker(marker)
                
#         print(f"Total de marcadores eliminados: {len(markers_to_remove)}")

    

#     def reiniciar_mapa(self):
#         print("Reiniciando MapView: Sustituyendo la instancia.")
        
#         # 1. Verificar y obtener referencias
#         if 'map_view' not in self.ids or 'mapa' not in self.ids:
#             print("Error: No se encontraron los IDs 'map_view' o 'map_container'.")
#             return
            
#         old_map_view = self.ids.mapa_view
#         map_container = self.ids.mapa
        
#         # 2. Obtener estado actual (para mantener la ubicación si es necesario)
#         current_lat = old_map_view.lat
#         current_lon = old_map_view.lon
#         current_zoom = old_map_view.zoom
        
#         # 3. Limpieza de la instancia antigua
#         # Llama a tu función de limpieza para detener timers, animaciones y eliminar marcadores
#         # Si Cerrar_Ventana no acepta un argumento, debe usar self.ids.map_view internamente
#         # Asumo que tu Cerrar_Ventana maneja la limpieza de timers y popups
#         if hasattr(self, 'Cerrar_Ventana'):
#             self.Cerrar_Ventana() # Llama a la limpieza profunda
            
#         # 4. Remover la instancia antigua del contenedor
#         map_container.remove_widget(old_map_view)
        
#         # 5. Crear la nueva instancia limpia (usando Factory.AgregarMapa)
#         # Esto asegura que todas las propiedades definidas en KV se apliquen
#         new_map_view = Factory.AgregarMapa(
#             id='map_view', # Reasignar el ID para mantener la funcionalidad de self.ids
#             lat=current_lat, 
#             lon=current_lon, 
#             zoom=current_zoom,
#             # Asegúrate de pasar las propiedades del root (layout) que MapView necesita
#             parent=self # Pasar self como parent para acceder a latitud, longitud, etc.
#         )
        
#         # 6. Añadir la nueva instancia al contenedor
#         # Como era el único hijo del contenedor, simplemente lo añadimos
#         map_container.add_widget(new_map_view)
        
#         # 7. Ejecutar la lógica de inicio del mapa (si Iniciar_Ventana() lo requiere)
#         # Aquí puedes llamar a la lógica que añade el marcador inicial, si lo haces aquí:
#         # self.Iniciar_Ventana() 

#         print("MapView reemplazado y limpio. Listo para ser usado.")

#     def on_map_updated(self, *args):
#         # Esta función se llama cuando el mapa se mueve o actualiza
#         map_view = self.ids.map_view
#         if map_view and hasattr(map_view, '_tiles'):
#             # Limpiar tiles antiguos
#             map_view._tiles.clear()
#             Window.canvas.ask_update()
    
#     @staticmethod
#     def configure_logging():
#         # Configurar loggers específicos
#         loggers = [
#             'urllib3.connectionpool',
#             'kivy_garden.mapview.downloader',
#             'kivy_garden.mapview.view',
#             'kivy.network.urlrequest'
#         ]
#         for logger_name in loggers:
#             logger = logging.getLogger(logger_name)
#             logger.setLevel(logging.WARNING)
    
#     def buscar_y_limpiar_cache(self):
#         try:
#             # Limpiar el directorio .cache
#             dot_cache_dir = os.path.join(os.getcwd(), '.cache')
#             if os.path.exists(dot_cache_dir):
#                 print(f"Limpiando .cache en: {dot_cache_dir}")
#                 shutil.rmtree(dot_cache_dir)
#                 print("Directorio .cache eliminado")

#             # Gestionar el directorio cache y sus contenidos
#             cache_dir = os.path.join(os.getcwd(), 'cache')
#             if os.path.exists(cache_dir):
#                 print(f"Gestionando caché en: {cache_dir}")
                
#                 # Obtener lista de archivos de caché con sus timestamps
#                 cache_files = []
#                 for file in os.listdir(cache_dir):
#                     if file.startswith('custom_map_'):
#                         file_path = os.path.join(cache_dir, file)
#                         try:
#                             # Obtener el tiempo de modificación del archivo
#                             mtime = os.path.getmtime(file_path)
#                             cache_files.append((mtime, file_path, file))
#                         except Exception as e:
#                             print(f"Error al procesar {file}: {e}")
                
#                 # Ordenar archivos por tiempo de modificación (más reciente primero)
#                 cache_files.sort(reverse=True)
                
#                 # Mantener solo los 4 archivos más recientes
#                 for i, (mtime, file_path, file_name) in enumerate(cache_files):
#                     if i >= 12:  # Eliminar todos excepto los primeros 4
#                         try:
#                             os.remove(file_path)
#                         except Exception as e:pass
#                     else:pass

#             return True
#         except Exception as e:
#             print(f"Error durante la gestión del caché: {e}")
#             return False

#     def limpiar_cache(self, *args):
#         try:
            
#             # Intentar limpiar el caché del sistema de archivos
#             self.buscar_y_limpiar_cache()
            
#             # Obtener referencia al MapView
#             if not hasattr(self, 'ids') or 'map_view' not in self.ids:
#                 return
            
#             map_view = self.ids.map_view
#             print(f"MapView encontrado: {map_view}")
            
#             # Limpiar tiles del mapa
#             if hasattr(map_view, '_tiles'):
#                 map_view._tiles.clear()
#                 print("_tiles limpiados")
            
#             if hasattr(map_view, 'tiles'):
#                 map_view.tiles = {}
#                 print("tiles limpiados")
                
#             # Limpiar caché del MapSource si existe
#             if hasattr(map_view, 'map_source') and hasattr(map_view.map_source, 'cache'):
#                 map_view.map_source.cache = {}
#                 print("Caché del MapSource limpiado")
            
#             # Forzar actualización
#             map_view.zoom = map_view.zoom
#             Window.canvas.ask_update()
#             print("Forzada actualización del mapa")
            
#             print("--- Limpieza de caché completada ---\n")
            
#         except Exception as e:
#             print(f"Error durante la limpieza del caché: {e}")

    
            
#     def _initialize_location(self, dt):
#         print("Iniciando búsqueda de ubicación...")
#         self.get_location_once()
        
#     def request_android_permissions(self):
#         try:
#             from android.permissions import request_permissions, Permission
#             request_permissions([Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION])
#         except Exception as e:
#             # No estamos en Android o módulo no disponible en PC
#             print("No se pudieron pedir permisos (no Android o ya otorgados):", e)

#     def get_location_once(self, timeout=10):
#         if platform == "android":
#             # En Android usamos GPS
#             self.request_android_permissions()
#             try:
#                 gps.configure(on_location=self._on_location, on_status=self._on_status)
#                 gps.start(minTime=1000, minDistance=0)
#                 self._gps_timeout_ev = Clock.schedule_once(self._on_gps_timeout, timeout)
#             except NotImplementedError:
#                 print("GPS no implementado en Android")
#                 self._get_location_by_ip()
#         else:
#             # En Windows usamos geolocalización por IP
#             self._get_location_by_ip()

#     def _get_location_by_ip(self):
#         print("Obteniendo ubicación por IP...")
#         try:
#             # Intentar primero con ip-api.com (más confiable)
#             def got_json(req, result):
#                 try:
#                     location_data = {
#                         'lat': str(result.get('lat', result.get('latitude', -33.4569400))),
#                         'lon': str(result.get('lon', result.get('longitude', -70.6482700))),
#                         'city': result.get('city', 'Santiago'),
#                         'region': result.get('region', 'Región Metropolitana'),
#                         'country': result.get('country', 'Chile')
#                     }
#                     self._on_location(**location_data)
#                 except Exception as e:
#                     print(f"Error procesando respuesta: {e}")
#                     self._on_location(lat="-33.4569400", lon="-70.6482700")

#             def on_error(req, error):
#                 print(f"Error en la solicitud: {error}")
#                 # Si falla, usar coordenadas por defecto
#                 self._on_location(lat="-33.4569400", lon="-70.6482700")

#             # Usar ip-api.com (más confiable y sin límites estrictos)
#             UrlRequest(
#                 "http://ip-api.com/json/",
#                 on_success=got_json,
#                 on_error=on_error,
#                 timeout=15
#             )
#         except Exception as e:
#             self._on_location(lat="-33.4569400", lon="-70.6482700")
            
#         except Exception as e:
#             # Coordenadas por defecto (puedes ajustarlas)
#             self._on_location(lat="-33.4569400", lon="-70.6482700")  # Santiago, Chile
            
            
#     def _on_location(self, **kwargs):
#         # cancelamos el timeout si llegó la ubicación
#         if hasattr(self, "_gps_timeout_ev"):
#             try: self._gps_timeout_ev.cancel()
#             except Exception: pass

#         try:
#             # Obtener y convertir coordenadas
#             lat = float(kwargs.get('lat') or kwargs.get('latitude', -33.4569400))
#             lon = float(kwargs.get('lon') or kwargs.get('longitude', -70.6482700))
            
#             # Actualizar propiedades
#             self.latitud = lat
#             self.longitud = lon
#             self.zoom = 15
#             self.ubicacion_actualizada = True  # Indicar que tenemos nuevas coordenadas
            
#             print("Ubicación recibida (una vez):", lat, lon)
            
#             # Si hay información adicional de la ciudad (desde IP)
#             if 'city' in kwargs:
#                 print(f"Ciudad: {kwargs.get('city')}, Región: {kwargs.get('region')}, País: {kwargs.get('country')}")
                
#         except ValueError as e:
#             pass#print(f"Error al convertir coordenadas: {e}")
#         except Exception as e:
#             pass#print(f"Error al actualizar ubicación: {e}")

#         # procesar la ubicación (actualizar UI, guardar, etc.)
#         # ...
        
#         # detener el GPS para que solo se reciba una vez
#         try:
#             gps.stop()
#         except Exception:
#             pass

#     def on_stop_gps(self):
#         try:
#             self.gps.stop()
#         except Exception:
#             pass
        
#     def _on_gps_timeout(self, dt):
#         print("Timeout: no se obtuvo ubicación en el tiempo esperado")
#         try:
#             gps.stop()
#         except Exception:
#             pass

