import requests
import json
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition


# ¡OJO! Esto ahora es tu PROJECT_ID, no la URL de la base de datos.
# Lo encuentras en la Configuración de tu proyecto en Firebase.
PROJECT_ID = "eva3-72fb2"

# Esta es la URL de la API REST de Firestore.
# Siempre tiene esta estructura, solo cambia tu PROJECT_ID.
FIRESTORE_API_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"







def _formatear_datos_firestore(datos):
        """
        Convierte un diccionario simple en el formato requerido por Firestore.
        Firestore espera que cada campo tenga un tipo explícito.
        """
        datos_formateados = {}
        for clave, valor in datos.items():
            if isinstance(valor, str):
                datos_formateados[clave] = {'stringValue': valor}
            elif isinstance(valor, int):
                datos_formateados[clave] = {'integerValue': str(valor)}
            # Agrega más tipos según sea necesario (boolean, double, etc.)
            else:
                raise ValueError(f"Tipo de dato no soportado para la clave '{clave}': {type(valor)}")
        return {'fields': datos_formateados}
        

class Layout_Registrar_L(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Registrar_L,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
    
    def Regresar_Login(self):
        self.abrir_otra_pantalla("AA_Login",SlideTransition(direction="right"))

    ################################################################################
    # --- FUNCIONES AUXILIARES PARA FIRESTORE ---
    ################################################################################


    # --- FUNCIÓN DE REGISTRO ADAPTADA A FIRESTORE ---
    def registrar_usuario_firestore(self, alias,apellidos,contrasena,correo,edad,nombres,rut,telefono):
        
        print(f"Registrando en FIRESTORE al usuario: {alias}")

        # 1. Elige una "colección" (como una carpeta). La llamaremos "usuarios".
        coleccion = "Registro"
        
        # 2. Elige un "ID de documento" (la clave única).
        #    Usar el 'rut' o 'nombre_usuario' es buena idea. Usaré 'rut'.
        id_documento = rut

        # 3. Crea el diccionario simple (igual que antes)
        datos_usuario = {
            'rut': rut,
            'nombres': nombres,
            'apellidos': apellidos,
            'edad': edad,
            'telefono': telefono,
            'alias': alias,
            'correo': correo,
            'contrasena': contrasena,
            'rol': 'Estandar'
        }
        
        # 4. Convierte los datos al formato de Firestore
        payload_firestore = _formatear_datos_firestore(datos_usuario)
        
        # 5. Construye la URL de destino
        #    .../documents/[COLECCION]/[ID_DEL_DOCUMENTO]
        ruta_documento = f"{FIRESTORE_API_URL}/{coleccion}/{id_documento}"
        
        try:
            # 6. Envía los datos usando PATCH.
            #    (PATCH crea el documento si no existe, o lo actualiza si ya existe)
            response = requests.patch(ruta_documento, data=json.dumps(payload_firestore))
            
            # (Opcional) Verificar si salió bien
            if response.status_code == 200:
                print("¡Usuario registrado y guardado en Firestore exitosamente!")
                self.Regresar_Login()
            else:
                # Imprime el error que da Google para más detalles
                print(f"Error al guardar en Firestore: {response.status_code}")
                print(response.json()) 

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}")