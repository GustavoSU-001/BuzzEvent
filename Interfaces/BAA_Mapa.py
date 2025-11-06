from kivy.uix.actionbar import BoxLayout
from kivy_garden.mapview import MapView, MapMarker
from kivy.utils import platform
from plyer import gps
from kivy.clock import Clock
import urllib.request
import json
import socket
import os
import logging
import shutil
from kivy.network.urlrequest import UrlRequest
from pathlib import Path
from functools import partial

# Configurar logging
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('kivy').setLevel(logging.WARNING)
os.environ['KIVY_NO_FILELOG'] = '1'  # Desactivar logging a archivo
os.environ['KIVY_NO_CONSOLELOG'] = '1'  # Desactivar logging a consola




from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.core.window import Window

class Layout_Mapa(BoxLayout):
    latitud = NumericProperty(-33.4569400)  # Santiago por defecto
    longitud = NumericProperty(-70.6482700)
    zoom = NumericProperty(12)
    marker = ObjectProperty(None)
    ubicacion_actualizada = BooleanProperty(False)  # Para controlar cuando actualizar el marcador

    def on_map_updated(self, *args):
        # Esta función se llama cuando el mapa se mueve o actualiza
        map_view = self.ids.map_view
        if map_view and hasattr(map_view, '_tiles'):
            # Limpiar tiles antiguos
            map_view._tiles.clear()
            Window.canvas.ask_update()
    
    @staticmethod
    def configure_logging():
        # Configurar loggers específicos
        loggers = [
            'urllib3.connectionpool',
            'kivy_garden.mapview.downloader',
            'kivy_garden.mapview.view',
            'kivy.network.urlrequest'
        ]
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.WARNING)
    
    def buscar_y_limpiar_cache(self):
        try:
            # Limpiar el directorio .cache
            dot_cache_dir = os.path.join(os.getcwd(), '.cache')
            if os.path.exists(dot_cache_dir):
                print(f"Limpiando .cache en: {dot_cache_dir}")
                shutil.rmtree(dot_cache_dir)
                print("Directorio .cache eliminado")

            # Gestionar el directorio cache y sus contenidos
            cache_dir = os.path.join(os.getcwd(), 'cache')
            if os.path.exists(cache_dir):
                print(f"Gestionando caché en: {cache_dir}")
                
                # Obtener lista de archivos de caché con sus timestamps
                cache_files = []
                for file in os.listdir(cache_dir):
                    if file.startswith('custom_map_'):
                        file_path = os.path.join(cache_dir, file)
                        try:
                            # Obtener el tiempo de modificación del archivo
                            mtime = os.path.getmtime(file_path)
                            cache_files.append((mtime, file_path, file))
                        except Exception as e:
                            print(f"Error al procesar {file}: {e}")
                
                # Ordenar archivos por tiempo de modificación (más reciente primero)
                cache_files.sort(reverse=True)
                
                # Mantener solo los 4 archivos más recientes
                for i, (mtime, file_path, file_name) in enumerate(cache_files):
                    if i >= 6:  # Eliminar todos excepto los primeros 4
                        try:
                            os.remove(file_path)
                            print(f"Archivo eliminado (antiguo): {file_name}")
                        except Exception as e:
                            print(f"Error al eliminar {file_name}: {e}")
                    else:
                        print(f"Manteniendo archivo reciente: {file_name}")

            return True
        except Exception as e:
            print(f"Error durante la gestión del caché: {e}")
            return False

    def limpiar_cache(self, *args):
        try:
            print("\n--- Iniciando limpieza de caché ---")
            
            # Intentar limpiar el caché del sistema de archivos
            self.buscar_y_limpiar_cache()
            
            # Obtener referencia al MapView
            if not hasattr(self, 'ids') or 'map_view' not in self.ids:
                print("Error: No se puede acceder al map_view")
                return
            
            map_view = self.ids.map_view
            print(f"MapView encontrado: {map_view}")
            
            # Limpiar tiles del mapa
            if hasattr(map_view, '_tiles'):
                map_view._tiles.clear()
                print("_tiles limpiados")
            
            if hasattr(map_view, 'tiles'):
                map_view.tiles = {}
                print("tiles limpiados")
                
            # Limpiar caché del MapSource si existe
            if hasattr(map_view, 'map_source') and hasattr(map_view.map_source, 'cache'):
                map_view.map_source.cache = {}
                print("Caché del MapSource limpiado")
            
            # Forzar actualización
            map_view.zoom = map_view.zoom
            Window.canvas.ask_update()
            print("Forzada actualización del mapa")
            
            print("--- Limpieza de caché completada ---\n")
            
        except Exception as e:
            print(f"Error durante la limpieza del caché: {e}")

    def __init__(self, abrir_otra_pantalla, **kwargs):
        print("Iniciando Layout_Mapa...")
        
        # Asegurarse de que no haya caché al inicio
        self.buscar_y_limpiar_cache()
        
        # Configurar logging antes de inicializar
        self.configure_logging()
        super(Layout_Mapa,self).__init__(**kwargs)
        
        # Obtener ubicación después de que el widget esté listo
        Clock.schedule_once(self._initialize_location, 2)
        
        # Programar limpieza periódica del caché
        Clock.schedule_interval(self.limpiar_cache, 5)  # Cada 5 segundos
        
        print("Layout_Mapa inicializado")
            
    def _initialize_location(self, dt):
        print("Iniciando búsqueda de ubicación...")
        self.get_location_once()
        
    def request_android_permissions(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION])
        except Exception as e:
            # No estamos en Android o módulo no disponible en PC
            print("No se pudieron pedir permisos (no Android o ya otorgados):", e)

    def get_location_once(self, timeout=10):
        if platform == "android":
            # En Android usamos GPS
            self.request_android_permissions()
            try:
                gps.configure(on_location=self._on_location, on_status=self._on_status)
                gps.start(minTime=1000, minDistance=0)
                self._gps_timeout_ev = Clock.schedule_once(self._on_gps_timeout, timeout)
            except NotImplementedError:
                print("GPS no implementado en Android")
                self._get_location_by_ip()
        else:
            # En Windows usamos geolocalización por IP
            self._get_location_by_ip()

    def _get_location_by_ip(self):
        print("Obteniendo ubicación por IP...")
        try:
            # Intentar primero con ip-api.com (más confiable)
            def got_json(req, result):
                try:
                    location_data = {
                        'lat': str(result.get('lat', result.get('latitude', -33.4569400))),
                        'lon': str(result.get('lon', result.get('longitude', -70.6482700))),
                        'city': result.get('city', 'Santiago'),
                        'region': result.get('region', 'Región Metropolitana'),
                        'country': result.get('country', 'Chile')
                    }
                    self._on_location(**location_data)
                except Exception as e:
                    print(f"Error procesando respuesta: {e}")
                    self._on_location(lat="-33.4569400", lon="-70.6482700")

            def on_error(req, error):
                print(f"Error en la solicitud: {error}")
                # Si falla, usar coordenadas por defecto
                self._on_location(lat="-33.4569400", lon="-70.6482700")

            # Usar ip-api.com (más confiable y sin límites estrictos)
            UrlRequest(
                "http://ip-api.com/json/",
                on_success=got_json,
                on_error=on_error,
                timeout=15
            )
        except Exception as e:
            self._on_location(lat="-33.4569400", lon="-70.6482700")
            
        except Exception as e:
            # Coordenadas por defecto (puedes ajustarlas)
            self._on_location(lat="-33.4569400", lon="-70.6482700")  # Santiago, Chile
            
            
    def _on_location(self, **kwargs):
        # cancelamos el timeout si llegó la ubicación
        if hasattr(self, "_gps_timeout_ev"):
            try: self._gps_timeout_ev.cancel()
            except Exception: pass

        try:
            # Obtener y convertir coordenadas
            lat = float(kwargs.get('lat') or kwargs.get('latitude', -33.4569400))
            lon = float(kwargs.get('lon') or kwargs.get('longitude', -70.6482700))
            
            # Actualizar propiedades
            self.latitud = lat
            self.longitud = lon
            self.zoom = 15
            self.ubicacion_actualizada = True  # Indicar que tenemos nuevas coordenadas
            
            print("Ubicación recibida (una vez):", lat, lon)
            
            # Si hay información adicional de la ciudad (desde IP)
            if 'city' in kwargs:
                print(f"Ciudad: {kwargs.get('city')}, Región: {kwargs.get('region')}, País: {kwargs.get('country')}")
                
        except ValueError as e:
            pass#print(f"Error al convertir coordenadas: {e}")
        except Exception as e:
            pass#print(f"Error al actualizar ubicación: {e}")

        # procesar la ubicación (actualizar UI, guardar, etc.)
        # ...
        
        # detener el GPS para que solo se reciba una vez
        try:
            gps.stop()
        except Exception:
            pass

    def on_stop_gps(self):
        try:
            self.gps.stop()
        except Exception:
            pass
        
    def _on_gps_timeout(self, dt):
        print("Timeout: no se obtuvo ubicación en el tiempo esperado")
        try:
            gps.stop()
        except Exception:
            pass

