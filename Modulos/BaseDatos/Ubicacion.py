import requests
import time
from typing import Optional, Dict, Any, Tuple

# --- Manejo de PLYER ---
try:
    # Importar Plyer para acceso al GPS nativo
    from plyer import gps
    PLYER_GPS_AVAILABLE = True
except ImportError:
    # Si Plyer no está instalado o no es compatible con el sistema operativo
    PLYER_GPS_AVAILABLE = False
    
# Clase Listener para Plyer (Necesario para manejar la naturaleza asíncrona del GPS)
class _GPSListener:
    """Clase auxiliar para capturar el resultado del callback de Plyer."""
    def __init__(self):
        self.location: Optional[Tuple[float, float]] = None
        self.found = False
        self.error = False

    def on_location(self, **kwargs):
        """Callback de éxito de Plyer."""
        if 'lat' in kwargs and 'lon' in kwargs:
            self.location = (float(kwargs['lat']), float(kwargs['lon']))
            self.found = True
            # Detenemos el GPS una vez que encontramos la ubicación
            gps.stop() 
        else:
            self.on_error()

    def on_error(self, **kwargs):
        """Callback de error de Plyer."""
        self.error = True
        gps.stop()


class LocationService:
    """
    Clase dedicada a la obtención de coordenadas geográficas.
    Prioriza GPS/Plyer, luego usa la IP, y utiliza geocodificación para lugares específicos.
    """

    def __init__(self):
        print("Servicio de Localización inicializado.")
        if not PLYER_GPS_AVAILABLE:
            print("⚠️ Advertencia: Plyer (GPS) no está disponible. Se usará el Fallback por IP.")

    # ------------------------------------------------------------------
    # --- MÉTODOS PRIVADOS DE OBTENCIÓN DE DATOS ---
    # ------------------------------------------------------------------

    def _get_location_by_ip(self) -> Optional[Tuple[float, float, str]]:
        """
        Método privado para obtener la ubicación aproximada por IP.
        :return: (latitud, longitud, ciudad_pais) o None.
        """
        try:
            # Endpoint público de geolocalización (ip-api.com)
            response = requests.get('http://ip-api.com/json', timeout=5)
            response.raise_for_status() 
            data = response.json()

            if data.get('status') == 'success':
                lat = data.get('lat')
                lon = data.get('lon')
                city_country = f"{data.get('city', 'N/A')}, {data.get('country', 'N/A')}"
                return float(lat), float(lon), city_country
            
            print(f"Error en API de IP: {data.get('message', 'Desconocido')}")
            return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión al obtener IP: {e}")
            return None
        except Exception as e:
            print(f"Error general en IP lookup: {e}")
            return None

    def _get_location_by_gps(self, timeout_sec: int = 10) -> Optional[Tuple[float, float]]:
        """
        Método para intentar obtener la ubicación vía Plyer GPS. 
        Requiere un entorno móvil/compatible con Plyer.
        :param timeout_sec: Tiempo máximo de espera para la señal GPS.
        :return: (latitud, longitud) o None.
        """
        if not PLYER_GPS_AVAILABLE:
            return None

        listener = _GPSListener()
        
        try:
            gps.configure(on_location=listener.on_location, on_error=listener.on_error)
            gps.start(minTime=1000, minDistance=1) # 1 segundo o 1 metro
            print(f"Esperando {timeout_sec} segundos por señal GPS...")

            # Mecanismo de espera SÍNCRONO (no ideal, pero funcional fuera de Kivy)
            start_time = time.time()
            while not listener.found and not listener.error and (time.time() - start_time) < timeout_sec:
                time.sleep(0.5) 

            gps.stop()
            
            if listener.found:
                print("Ubicación GPS obtenida.")
                return listener.location
            elif listener.error:
                print("Error al obtener ubicación GPS.")
                return None
            else:
                print(f"Tiempo límite de {timeout_sec} segundos excedido para GPS.")
                return None

        except Exception as e:
            print(f"Error en la inicialización de Plyer GPS: {e}")
            return None

    # ------------------------------------------------------------------
    # --- MÉTODOS PÚBLICOS SOLICITADOS ---
    # ------------------------------------------------------------------

    def obtener_mi_ubicacion(self) -> Dict[str, Any]:
        """
        Intenta obtener la ubicación precisa por GPS (si es móvil) 
        y recurre a la ubicación aproximada por IP si falla.
        :return: Diccionario con latitud, longitud, fuente y mensaje.
        """
        # 1. Intento por GPS/Plyer
        gps_location = self._get_location_by_gps(timeout_sec=10)
        
        if gps_location:
            lat, lon = gps_location
            return {
                "latitud": lat,
                "longitud": lon,
                "fuente": "GPS/Plyer (Dispositivo)",
                "mensaje": "Ubicación precisa obtenida mediante el dispositivo."
            }

        # 2. Fallback por IP
        ip_location = self._get_location_by_ip()
        
        if ip_location:
            lat, lon, ciudad_pais = ip_location
            return {
                "latitud": lat,
                "longitud": lon,
                "fuente": "IP (Aproximada)",
                "mensaje": f"Ubicación aproximada obtenida por IP ({ciudad_pais})."
            }

        # 3. Falla total
        return {
            "latitud": None,
            "longitud": None,
            "fuente": "Ninguna",
            "mensaje": "Fallo total al obtener la ubicación. Revise la conexión y permisos."
        }

    def obtener_coordenadas_de_lugar(self, lugar: str) -> Dict[str, Any]:
        """
        Obtiene las coordenadas (Lat/Lon) de un lugar (ciudad, dirección, etc.)
        mediante el servicio de geocodificación Nominatim (OpenStreetMap).

        :param lugar: El nombre del lugar a buscar (ej: 'Santiago de Chile').
        :return: Diccionario con latitud, longitud y fuente/nombre encontrado.
        """
        if not lugar:
            return {
                "latitud": None,
                "longitud": None,
                "fuente": "Geocodificación",
                "mensaje": "El lugar de búsqueda no puede estar vacío."
            }
            
        try:
            # Usamos Nominatim (OpenStreetMap) para geocodificación inversa
            url = 'https://nominatim.openstreetmap.org/search'
            params = {
                'q': lugar,
                'format': 'json',
                'limit': 1 
            }
            headers = {
                # Se requiere un User-Agent para Nominatim
                'User-Agent': 'BuzzEventLocationService/1.0' 
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status() 
            data = response.json()

            if data and isinstance(data, list) and len(data) > 0:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                display_name = result['display_name']
                
                return {
                    "latitud": lat,
                    "longitud": lon,
                    "fuente": "Geocodificación (Nominatim)",
                    "nombre_encontrado": display_name,
                    "mensaje": f"Coordenadas encontradas para: {display_name}"
                }
            
            return {
                "latitud": None,
                "longitud": None,
                "fuente": "Geocodificación (Nominatim)",
                "mensaje": f"No se encontraron coordenadas para el lugar: {lugar}"
            }
                
        except requests.exceptions.RequestException as e:
            return {
                "latitud": None,
                "longitud": None,
                "fuente": "Geocodificación (Nominatim)",
                "mensaje": f"Error de conexión al buscar lugar: {e}"
            }
        except Exception as e:
            return {
                "latitud": None,
                "longitud": None,
                "fuente": "Geocodificación (Nominatim)",
                "mensaje": f"Error interno al buscar lugar: {e}"
            }