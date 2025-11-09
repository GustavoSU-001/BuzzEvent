import requests
import json
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.popup import Popup #Para mostrar errores
from kivy.uix.label import Label #label para el popup

#ID del proyecto de Firebase
PROJECT_ID = "eva3-72fb2"

# Esta es la URL de la API REST de Firestore.
FIRESTORE_API_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"



def _formatear_datos_firestore(datos):
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

    def mostrar_popup(self, titulo, mensaje):   #funcion para mostrar popups y reutilizable
        popup = Popup(
            title=titulo,
            content=Label(text=mensaje),
            size_hint=(None, None), size=(400, 200)
        )
        popup.open()
    
    def Regresar_Login(self):
        self.limpiar_campos()
        self.abrir_otra_pantalla("AA_Login",SlideTransition(direction="right"))

    ################################################################################
    # --- FUNCIONES AUXILIARES PARA FIRESTORE ---
    ################################################################################


    # --- FUNCIÓN DE REGISTRO ADAPTADA A FIRESTORE y termino y condiciones ---
    def registrar_usuario_firestore(self, alias,apellidos,contrasena,correo,edad_texto,nombres,rut,telefono_texto):
        
        campos_text=[alias,apellidos,contrasena,correo,edad_texto,nombres,rut,telefono_texto]

        if not all(campoo.strip() for campoo in campos_text):
            self.mostrar_popup("Error de Registro", "Todos los campos son obligatorios llenar para el registro.")
            return  # Se detiene la funcion si hay campos vacios 
        try:
            if not self.ids.terminos_y_condiciones.ids.checkbox_Registrar_L.active:
                popup=Popup(
                    title="Términos y Condiciones", #titulo del popup
                    content=Label(text="Debe aceptar los términos y condiciones para registrarse."),# Lo que contiene
                    size_hint=(None, None), size=(400, 200) #tamaño del popup
                )
                popup.open()
                return  # Detenemos la función si no se aceptan los términos
        except AttributeError as e:
            print(f"Error al verificar términos y condiciones: {e}. Asegúrate de que el ID en el .kv coincida.")
            return  # Detenemos la función si hay un error


        print(f"Registrando en FIRESTORE al usuario: {alias}")

        #convertir de string a numero "edad"
        try:
            edad_numero = int(edad_texto)
        except ValueError:
            print(f"Error: La edad '{edad_texto}' no es un número válido.")
            return # Detenemos

       #convertir de string a numero "telefono"
        try:
            telefono_numero = int(telefono_texto)
        except ValueError:
            # Esto fallará si escriben "+", espacios o guiones
            print(f"Error: El teléfono '{telefono_texto}' no es un número válido.")
            return # Detenemos
        # --------------------


        # 1. Elegir la coleccion
        coleccion = "Registro"
        
        #Docuemnento ID unico o basado en algun campo unico
        id_documento = rut

        # 3. Crear un diccionario con los datos del usuario
        datos_usuario = {
            'rut': rut,
            'nombres': nombres,
            'apellidos': apellidos,
            'edad': edad_numero,
            'telefono': telefono_numero,
            'alias': alias,
            'correo': correo,
            'contrasena': contrasena,
            'rol': 'Estandar'
        }
        
        # 4. Convierte los datos al formato de Firestore
        payload_firestore = _formatear_datos_firestore(datos_usuario)
        
        # 5. Construye la URL de destino , coleccion y documento
        ruta_documento = f"{FIRESTORE_API_URL}/{coleccion}"
        
        try:
            # 6. Envía los datos usando PATCH.
            #response = requests.patch(ruta_documento, data=json.dumps(payload_firestore))

            response= requests.post(ruta_documento, params={'documentId': id_documento}, data=json.dumps(payload_firestore))
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            self.mostrar_popup("Registro Exitoso", "¡Usuario registrado exitosamente!") # registro del usuario de manera exitosa 
            self.limpiar_campos()
            
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 409:
                self.mostrar_popup("Error de Registro", "El usuario con este RUT ya existe.") # en caso que el rut exista arroje un mensaje
            else:
                #en caso de que el registro tenga un error distinto
                self.mostrar_popup("Error de Registro", f"Error al guardar en Firestore: {err.response.status_code}")
                print(f"Detalles del error: {err.response.json()}")
                #en caso que el registro tenga un error distinto
        except requests.exceptions.RequestException as e:
            self.mostrar_popup("Error de Conexión", f"Error de conexión: {e}")
            print(f"Error de conexión: {e}")


################################################################################

# --- Funciona para limpiar los campos  ---
    def limpiar_campos(self):
        """
        Limpia los campos del formulario registro.
        """
        print("Limpiando campos de registro...")
        try:
            #Agregamos los id que estan en el .kv para limpiar los campos
            self.ids.alias_input.ids.usuario.text = ""
            self.ids.apellidos_input.ids.usuario.text = ""
            self.ids.contrasena_input.ids.usuario.text = ""
            self.ids.correo_input.ids.usuario.text = ""
            self.ids.edad_input.ids.usuario.text = ""
            self.ids.nombres_input.ids.usuario.text = ""
            self.ids.rut_input.ids.usuario.text = ""
            self.ids.telefono_input.ids.usuario.text = ""
            # Limpiar el chexbox de términos y condiciones
            self.ids.terminos_y_condiciones.ids.checkbox_Registrar_L.active = False
        except AttributeError as e:
            print(f"Error al limpiar campos: {e}. Asegúrate de que los IDs en el .kv coincidan.")
################################################################################  
