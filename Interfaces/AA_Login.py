import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
# --- NUEVOS IMPORTS PARA MENSAJES ---
from kivy.uix.popup import Popup
from kivy.uix.label import Label
# ------------------------------------
from Modulos.Singleton.Perfil import Singleton_Perfil
import uuid

# --- IMPORTACIONES DE FIREBASE ---
import firebase_admin
from firebase_admin import credentials, firestore
from kivy.clock import Clock # Importante para esperar a que cargue la interfaz

# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ==========================================
NOMBRE_ARCHIVO_JSON = "eva3-72fb2-firebase-adminsdk-hbxid-828018cca2.json" 

def encontrar_archivo_json(nombre_archivo):
    """Busca el archivo JSON recursivamente."""
    directorio_base = os.path.dirname(os.path.realpath(__file__))
    
    # 1. Busqueda hacia abajo
    for raiz, carpetas, archivos in os.walk(directorio_base):
        if nombre_archivo in archivos:
            return os.path.join(raiz, nombre_archivo)
            
    # 2. Busqueda hacia arriba (por si está en una subcarpeta)
    directorio_padre = os.path.dirname(directorio_base)
    for raiz, carpetas, archivos in os.walk(directorio_padre):
        if nombre_archivo in archivos:
            return os.path.join(raiz, nombre_archivo)
    return None

# --- INICIALIZACIÓN ---
db = None
ruta_credenciales = encontrar_archivo_json(NOMBRE_ARCHIVO_JSON)

if ruta_credenciales:
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(ruta_credenciales)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("--- [LOGIN] BD CONECTADA ---")
    except Exception as e:
        print(f"Error Conexión BD: {e}")
else:
    print("ERROR FATAL: JSON de credenciales no encontrado.")


# ==========================================
# CLASE DEL LAYOUT
# ==========================================

class Layout_Login(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Login,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        
        # Inicialización del Singleton (Sesión)
        try:
            self.perfil_sesion = Singleton_Perfil.get_instance()
            self.perfil_sesion.tipo_perfil = None
            self.perfil_sesion.rut = None
            self.perfil_sesion.token = None
        except Exception as e:
            print(f"Advertencia Singleton: {e}")

        # --- AUTO-VINCULACIÓN DE EVENTOS ---
        # Esperamos 0.5 segundos a que el archivo .kv cargue los IDs
        # y luego conectamos la lógica del RUT automáticamente.
        Clock.schedule_once(self.vincular_eventos_rut, 0.5)

    def vincular_eventos_rut(self, dt):
        """Busca el input del RUT y le conecta la lógica sin tocar el KV."""
        try:
            # 1. Buscamos el componente personalizado (Input_Login)
            if 'input_usuario' in self.ids:
                componente_padre = self.ids.input_usuario
                
                # 2. Buscamos el TextInput real adentro (id: usuario)
                if hasattr(componente_padre, 'ids') and 'usuario' in componente_padre.ids:
                    input_real = componente_padre.ids.usuario
                    
                    # 3. Conectamos las funciones (Bind)
                    # on_text -> limitar_input_rut
                    input_real.bind(text=self.limitar_input_rut)
                    # on_focus -> formatear_rut_al_salir
                    input_real.bind(focus=self.formatear_rut_al_salir)

                    
                    print("LOG: Lógica de RUT conectada exitosamente.")

            # 2. Vincular CONTRASEÑA (Nueva lógica)
            # Buscamos por ambos nombres posibles para evitar errores
            comp_pass = self.ids.get('input_contraseña') or self.ids.get('input_contrasena')
            
            if comp_pass and hasattr(comp_pass, 'ids') and 'usuario' in comp_pass.ids:
                pass_real = comp_pass.ids.usuario
                # Conectamos la función que limita a 16 caracteres
                pass_real.bind(text=self.limitar_input_password)
                print("LOG: Lógica Password conectada.")


        except Exception as e:
            print(f"Advertencia: No se pudo vincular lógica de RUT: {e}")

    def mostrar_error(self, mensaje):
        popup = Popup(
            title='Error de Ingreso',
            content=Label(text=mensaje),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()

    #-------------------------------------------------------------------------------

        # --- LÓGICA DE LIMPIEZA ---
    def limpiar_formulario(self, dt=None):
        """Limpia los campos de texto del login."""
        try:
            # Limpiar RUT
            if 'input_usuario' in self.ids:
                self.ids.input_usuario.ids.usuario.text = ""
            
            # Limpiar Contraseña
            if 'input_contraseña' in self.ids:
                self.ids['input_contraseña'].ids.usuario.text = ""
            elif 'input_contrasena' in self.ids:
                self.ids.input_contrasena.ids.usuario.text = ""
            
            print("LOG: Formulario Login Reseteado")
        except Exception as e:
            print(f"Error limpiando inputs: {e}")




    # --- LÓGICA DE RUT ---
    
    def limitar_input_rut(self, widget_input, texto_nuevo):
        """Limita caracteres (Llamado automáticamente por bind)."""
        texto = widget_input.text
        if not texto: return

        # Límite: 12 con formato, 9 sin formato
        limite = 12 if ('.' in texto or '-' in texto) else 9
        
        if len(texto) > limite:
            widget_input.text = texto[:limite]



    def formatear_rut_al_salir(self, widget_input, tiene_foco):
        """Formatea al salir (Llamado automáticamente por bind)."""
        if not tiene_foco: 
            texto_bruto = widget_input.text
            if not texto_bruto: return

            limpio = texto_bruto.replace(".", "").replace("-", "").replace(" ", "").upper()
            
            if len(limpio) < 2: return

            try:
                cuerpo = limpio[:-1]
                dv = limpio[-1]
                cuerpo_puntos = "{:,}".format(int(cuerpo)).replace(",", ".")
                rut_final = f"{cuerpo_puntos}-{dv}"
                widget_input.text = rut_final
            except ValueError:
                pass 
    # ----------------------------------------
        
    def Boton_recuperar_contrasena(self):
        self.limpiar_formulario()
        self.abrir_otra_pantalla("ABA_Recuperar_L", transition=SlideTransition(direction="left"))
        
    def Boton_registrar_cuenta(self):
        self.limpiar_formulario()
        self.abrir_otra_pantalla("ACA_Registrar_L", transition=SlideTransition(direction="left"))

    def Iniciar_Sesion(self, rut_ingresado, password_ingresada=None):
        """Lógica principal de Login."""
        
        if not password_ingresada:
            try:
                if 'input_contraseña' in self.ids:
                    password_ingresada = self.ids['input_contraseña'].ids.usuario.text
                elif 'input_contrasena' in self.ids:
                    password_ingresada = self.ids.input_contrasena.ids.usuario.text
            except Exception as e:
                print(f"Error obteniendo password del UI: {e}")

        print(f"Intento de Login -> RUT: {rut_ingresado}")
        
        if not rut_ingresado or not password_ingresada:
            self.mostrar_error("Por favor complete RUT y Contraseña.")
            return

        if not db:
            self.mostrar_error("Error de conexión con la Base de Datos.")
            return

        try:
            doc_ref = db.collection('Registro').document('Usuario')
            doc = doc_ref.get()
            
            if not doc.exists:
                self.mostrar_error("Error del sistema: No existe registro de usuarios.")
                return

            data = doc.to_dict()
            rut_limpio = str(rut_ingresado).strip().upper() # Aseguramos formato
            
            # NOTA: Si al formatear queda "12.345.678-9" y en BD está "12345678-9",
            # podrías necesitar probar ambas versiones aquí.
            # Por ahora usamos la versión tal cual está en el input.

            if rut_limpio in data:
                datos_usuario = data[rut_limpio]
                pass_real = str(datos_usuario.get('contrasena', '')).strip()
                pass_user = str(password_ingresada).strip()
                
                if pass_real == pass_user:
                    print("¡LOGIN EXITOSO!")
                    rol_usuario = datos_usuario.get('rol', 'Estandar')
                    nombre_usuario = datos_usuario.get('nombres', '')
                    self.Configurar_Sesion_Y_Abrir(rut_limpio, rol_usuario, nombre_usuario)
                else:
                    self.mostrar_error("La contraseña es incorrecta.")
            else:
                self.mostrar_error("El RUT ingresado no se encuentra registrado.")
                
        except Exception as e:
            print(f"Excepción en Login: {e}")
            self.mostrar_error("Ocurrió un error inesperado al iniciar sesión.")




    # Distinto perfiles segun el rut y el rol
    def Configurar_Sesion_Y_Abrir(self, rut, rol, nombre):
        try:
            perfil = Singleton_Perfil.get_instance()
            perfil.rut = rut
            perfil.tipo_perfil = rol
            perfil.nombre = nombre
            perfil.token = uuid.uuid4().hex
        except Exception as e:
            print(f"Error guardando sesión: {e}")
        
        print(f"Redirigiendo usuario {rut} con rol {rol}...")

                # ---Limpieza al salirme de la cuenta  ---
        # Programamos la limpieza para 1 segundo después, cuando ya se haya cambiado de pantalla
        Clock.schedule_once(self.limpiar_formulario, 1)
        # ---------------------------------------------------
        
        if rol == "Estandar":
            self.abrir_otra_pantalla("BA_Estandar", transition=SlideTransition(direction="up"))
        elif rol == "Organizador":
            self.abrir_otra_pantalla("BB_Organizador", transition=SlideTransition(direction="up"))
        elif rol == "Administrador":
            self.abrir_otra_pantalla("BC_Administrador", transition=SlideTransition(direction="up"))
        else:
            print(f"ROL DESCONOCIDO: {rol}. Redirigiendo a Estandar.")
            self.abrir_otra_pantalla("BA_Estandar", transition=SlideTransition(direction="up"))

    ######## Limitador de contraseña ######
    def limitar_input_password(self, widget_input, texto_nuevo):
        """Limita la contraseña a máximo 16 caracteres."""
        texto = widget_input.text
        if not texto: return
        
        # Límite máximo estricto
        if len(texto) > 16:
            widget_input.text = texto[:16]

    # ----------------------------------------

    