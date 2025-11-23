from kivy.event import EventDispatcher
from kivy.properties import StringProperty
from kivy.utils import platform

# IMPORTANTE: Reemplaza esto con el import de la librería real que uses (ej: 'from sjbilling import SjBilling')
# Para este ejemplo, asumiremos que existe un wrapper llamado BillingService
if platform == 'android':
    try:
        from android_billing_wrapper import BillingService
    except ImportError:
        print("ADVERTENCIA: No se encontró el wrapper de facturación de Android. Las compras no funcionarán en el dispositivo.")
        # Clase Mock para evitar errores si no se encuentra el wrapper
        class BillingService:
            def __init__(self, key, callback): pass
            def connect(self): print("Mock: Conectando al servicio...")
            def query_product_details(self, ids): return {}
            def launch_purchase_flow(self, id): print(f"Mock: Iniciando compra para {id}")
            def is_product_purchased(self, id): return False
            def consume_purchase(self, id): print(f"Mock: Consumiendo compra {id}")

class BillingManager(EventDispatcher):
    '''
    Clase para gestionar la lógica de Google Play Billing.
    Hereda de EventDispatcher para enviar notificaciones a la UI (Kivy).
    '''
    # Propiedades para notificar a Kivy de cambios de estado
    connection_status = StringProperty('Desconectado')
    
    # Eventos que se pueden enlazar desde Kivy
    __events__ = ('on_purchase_success', 'on_purchase_failed', 'on_connected')

    def __init__(self, google_public_key, **kwargs):
        super().__init__(**kwargs)
        self.public_key = google_public_key
        self.billing_service = None
        self.products = {} # Para almacenar detalles de productos (precios, etc.)

    def setup(self):
        """Inicializa el servicio de facturación de Android."""
        if platform == 'android':
            # La BillingService necesita la clave pública y un objeto de callback (self)
            self.billing_service = BillingService(
                self.public_key, 
                callback_handler=self # Pasamos esta misma clase como manejador de callbacks
            )
            self.billing_service.connect()
        else:
            self.connection_status = 'Conexión local simulada'
            self.dispatch('on_connected')
            print("INFO: Modo de desarrollo. Se simula la conexión de facturación.")

    # --- Métodos Públicos para la Aplicación Kivy ---

    def query_product_details(self, product_ids):
        """Consulta los detalles (precio, etc.) de los IDs de producto."""
        if self.billing_service:
            # En un entorno real, esto llamaría a la API de Android y actualizaría self.products
            self.products = self.billing_service.query_product_details(product_ids)
            print("INFO: Detalles de productos consultados.")
            return self.products
        return {}
    
    def buy(self, product_id):
        """
        Método a llamar desde tu botón de Kivy.
        Inicia el flujo de compra de Google Play.
        """
        if platform == 'android' and self.billing_service:
            print(f"INFO: Llamando a Google Play para comprar {product_id}...")
            # Aquí se le pasa el ID al servicio nativo para abrir la ventana de Google Play
            self.billing_service.launch_purchase_flow(product_id)
        elif platform != 'android':
            print(f"INFO: Simulación de compra exitosa para {product_id}")
            # En modo desktop, simulamos el éxito para fines de desarrollo
            self.dispatch('on_purchase_success', product_id, "simulated_token")

    # --- Métodos de Callback de la API de Facturación ---
    # Estos métodos son llamados automáticamente por el wrapper (BillingService)
    # cuando Google Play responde.

    def on_billing_connected(self):
        """Se llama cuando el servicio de Google Play se conecta exitosamente."""
        self.connection_status = 'Conectado'
        self.dispatch('on_connected')
        print("INFO: Servicio de Google Play Billing conectado.")

    def on_purchase_result(self, product_id, purchase_token, status):
        """Maneja el resultado final de la compra."""
        if status == 'SUCCESS':
            print(f"COMPRA EXITOSA: Producto ID: {product_id}")
            # En un caso de uso real, aquí también harías la verificación en tu servidor
            self.dispatch('on_purchase_success', product_id, purchase_token)
            
            # Si es un artículo consumible, consúmelo inmediatamente para permitir otra compra
            # self.billing_service.consume_purchase(purchase_token) 
            
        elif status == 'CANCELLED':
            print("COMPRA CANCELADA por el usuario.")
            self.dispatch('on_purchase_failed', product_id, 'Compra cancelada.')
            
        elif status == 'FAILURE':
            print(f"COMPRA FALLIDA: {product_id}")
            self.dispatch('on_purchase_failed', product_id, 'Error de compra desconocido.')

    # --- Métodos del EventDispatcher ---

    def on_purchase_success(self, product_id, purchase_token):
        """Evento para cuando una compra fue exitosa (debe ser implementado en la App Kivy)."""
        pass

    def on_purchase_failed(self, product_id, reason):
        """Evento para cuando una compra falla (debe ser implementado en la App Kivy)."""
        pass
        
    def on_connected(self):
        """Evento para cuando la conexión se establece (debe ser implementado en la App Kivy)."""
        pass




