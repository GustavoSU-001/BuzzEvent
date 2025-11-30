import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys 

# Kivy Imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import SlideTransition
from kivy.clock import Clock

# Firebase Imports
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# SECCIÓN 1: CONFIGURACIÓN
# ==========================================

# Conexion a la base de datos
NOMBRE_ARCHIVO_JSON = "eva3-72fb2-firebase-adminsdk-hbxid-828018cca2.json" 

def encontrar_archivo_json(nombre_archivo):
    """Busca el archivo JSON recursivamente."""
    directorio_base = os.path.dirname(os.path.realpath(__file__))
    print(f"--- BUSCANDO '{nombre_archivo}' DESDE: {directorio_base} ---")
    
    for raiz, carpetas, archivos in os.walk(directorio_base):
        if nombre_archivo in archivos:
            return os.path.join(raiz, nombre_archivo)
            
    directorio_padre = os.path.dirname(directorio_base)
    for raiz, carpetas, archivos in os.walk(directorio_padre):
        if nombre_archivo in archivos:
            return os.path.join(raiz, nombre_archivo)

    return None

# --- INICIO DE CONEXIÓN ---
db = None
ruta_credenciales = encontrar_archivo_json(NOMBRE_ARCHIVO_JSON)

if ruta_credenciales:
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(ruta_credenciales)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        print("*** CONEXIÓN A BASE DE DATOS EXITOSA ***")
        
    except Exception as e:
        print(f"*** ERROR AL CONECTAR: {e}")
else:
    print(f"ERROR FATAL: No se encontró el archivo '{NOMBRE_ARCHIVO_JSON}'")


# ==========================================
# SECCIÓN 2: LÓGICA DE NEGOCIO
# ==========================================
codigo_secreto_generado = None
rut_usuario_encontrado = None 

def enviar_codigo_verificacion(destinatario, es_correo=True):
    global codigo_secreto_generado
    codigo_secreto_generado = str(random.randint(100000, 999999))
    
    if es_correo:
        # --- CONFIGURA TU GMAIL AQUÍ ---
        sender_email = "guille18.xd@gmail.com"  # <--- CAMBIAR
        sender_password = "dywc toiz dycb ougb"  # <--- CAMBIAR (Clave de 16 digitos)
        
        if sender_email == "tucorreo@gmail.com":
            print("\n!!! ERROR: Configura el sender_email en el código !!!\n")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = destinatario
        msg['Subject'] = "Codigo de Recuperacion"
        msg.attach(MIMEText(f"Tu codigo es: {codigo_secreto_generado}", 'plain'))
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, destinatario, msg.as_string())
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError:
            print("ERROR 535: Revisa tu Contraseña de Aplicación.")
            return False
        except Exception as e:
            print(f"Error SMTP: {e}")
            return False
    else:
        print(f"\n[SMS SIMULADO] Enviar a: {destinatario} | Código: {codigo_secreto_generado}\n")
        return True

def buscar_usuario_especifico(dato_ingresado):
    global rut_usuario_encontrado
    
    if db is None:
        print("ERROR: Sin conexión a BD.")
        return False
        
    try:
        doc_ref = db.collection('Registro').document('Usuario')
        doc = doc_ref.get()
        
        if not doc.exists: return False

        data = doc.to_dict()
        if not data: return False
        
        dato_limpio = str(dato_ingresado).strip()
        es_correo = "@" in dato_limpio
        
        for rut_key, user_data in data.items():
            if not isinstance(user_data, dict): continue 
            
            if es_correo and user_data.get('correo') == dato_limpio:
                rut_usuario_encontrado = rut_key 
                print(f"¡ENCONTRADO! RUT: {rut_key}") # arrojar un print para ver si detecto el rut que esta afiliado a ese correo
                return True
            
            if not es_correo:
                tel_bd = user_data.get('telefono')  # los mismo pero con la parte del telefono
                if str(tel_bd) == dato_limpio:
                     rut_usuario_encontrado = rut_key
                     return True
            
        print("DEBUG: No encontrado.")
        return False

    except Exception as e:
        print(f"Error Firestore: {e}")
        return False

def validar_codigo_interno(codigo_ingresado):
    return str(codigo_ingresado).strip() == str(codigo_secreto_generado)

def actualizar_contrasena_firestore(nueva_contra):
    global rut_usuario_encontrado
    if not db or not rut_usuario_encontrado: return False
    
    try:
        doc_ref = db.collection('Registro').document('Usuario')
        
        print(f"DEBUG: Actualizando contraseña para el RUT '{rut_usuario_encontrado}'...")
        
        # --- SOLUCIÓN ROBUSTA PARA RUTS CON PUNTOS ---
        # En lugar de usar FieldPath (que da errores en tu versión),
        # usamos un diccionario estructurado y merge=True.
        # Esto le dice a Firebase: "Toma este RUT, entra a 'contrasena' y actualízala,
        # pero NO borres el resto de los datos (merge)".
        
        datos_actualizar = {
            rut_usuario_encontrado: {
                'contrasena': nueva_contra
            }
        }
        
        doc_ref.set(datos_actualizar, merge=True)
        
        print("DEBUG: Actualización exitosa.")
        return True
    except Exception as e:
        print(f"Error Update: {e}")
        return False

# ==========================================
# SECCIÓN 3: INTERFAZ GRÁFICA (KIVY)
# ==========================================

class Layout_Recuperar_L(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Recuperar_L,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        self.Ingresar_Correo_o_Telefono()

    def _obtener_texto_seguro(self, widget):
        if hasattr(widget, 'text') and widget.text: return widget.text
        if hasattr(widget, 'texto') and widget.texto: return widget.texto
        try:
            for child in widget.walk():
                if isinstance(child, TextInput): return child.text
        except: pass
        return ""

    def _limpiar_texto_seguro(self, widget):
        try: widget.text = ""
        except: pass
        try: widget.texto = ""
        except: pass
        try:
            for child in widget.walk():
                if isinstance(child, TextInput): child.text = ""
        except: pass

    def Ingresar_Correo_o_Telefono(self, dt=None):
        self.ids.img_recuperar.size_hint_y = 0
        self.ids.img_recuperar.opacity = 0
        self.ids.lbl_recuperar.size_hint_y = 1
        self.ids.lbl_recuperar.text = "Ingrese su Correo Electrónico."

        self.ids.inp_recuperar_p.t_text = 'Correo Electrónico'
        self._limpiar_texto_seguro(self.ids.inp_recuperar_p)
        
        self.ids.inp_recuperar_p.opacity = 1
        self.ids.inp_recuperar_p.disabled = False
        #self.ids.box_btn_recuperar.size_hint_y = 0.5
        
        self.ids.btn_recuperar.text = 'Siguiente'
        self.ids.btn_recuperar.accion = self.Procesar_Usuario_BD
        
    def Procesar_Usuario_BD(self):
        dato = self._obtener_texto_seguro(self.ids.inp_recuperar_p)

        if not dato:
            self.ids.lbl_recuperar.text = "El campo está vacío."
            return

        self.ids.lbl_recuperar.text = "Buscando usuario..."

        if buscar_usuario_especifico(dato):
            es_email = "@" in dato
            if enviar_codigo_verificacion(dato, es_email):
                msg = f"Enviado a {dato}. Revise su correo electronico" if es_email else "SMS enviado"
                self.ids.lbl_recuperar.text = msg
                self.Ir_A_Verificar_Codigo()
            else:
                self.ids.lbl_recuperar.text = "Error al enviar correo."
        else:
            self.ids.lbl_recuperar.text = "Correo no encontrado."

    def Ir_A_Verificar_Codigo(self):
        self.ids.inp_recuperar_p.t_text = 'Código de Verificación'
        self._limpiar_texto_seguro(self.ids.inp_recuperar_p)
        self.ids.btn_recuperar.text = 'Verificar'
        self.ids.btn_recuperar.accion = self.Validar_Codigo_Ingresado

    def Validar_Codigo_Ingresado(self):
        codigo = self._obtener_texto_seguro(self.ids.inp_recuperar_p)
        if validar_codigo_interno(codigo):
            self.Guardar_Contrasena_UI()
        else:
            self.ids.lbl_recuperar.text = "Código Incorrecto."
    
    def Guardar_Contrasena_UI(self):
        self.ids.lbl_recuperar.text = "Ingrese nueva contraseña."
        self.ids.inp_recuperar_p.t_text = 'Nueva Contraseña'
        self._limpiar_texto_seguro(self.ids.inp_recuperar_p)
        
        self.ids.inp_recuperar_s.t_text = 'Confirmar Contraseña'
        self._limpiar_texto_seguro(self.ids.inp_recuperar_s)
        
        self.ids.inp_recuperar_s.opacity = 1
        self.ids.inp_recuperar_s.disabled = False
        
        self.ids.btn_recuperar.accion = self.Finalizar_Cambio
        self.ids.btn_recuperar.text = 'Cambiar'

    def Finalizar_Cambio(self):
        p1 = self._obtener_texto_seguro(self.ids.inp_recuperar_p)
        p2 = self._obtener_texto_seguro(self.ids.inp_recuperar_s)
        
        if p1 == p2 and len(p1) > 0:
            if actualizar_contrasena_firestore(p1):
                self.Resultado_Exitoso()
            else:
                self.ids.lbl_recuperar.text = "Error al guardar."
        else:
            self.ids.lbl_recuperar.text = "Las contraseñas no coinciden."
            
    def Resultado_Exitoso(self):
        self.ids.img_recuperar.size_hint_y = 0.5
        self.ids.img_recuperar.opacity = 1
        self.ids.lbl_recuperar.size_hint_y = 0.2
        self.ids.lbl_recuperar.text = "¡Éxito! Su Contraseña a sido cambiada."
        
        self.ids.inp_recuperar_p.opacity = 0; self.ids.inp_recuperar_p.disabled = True
        self.ids.inp_recuperar_s.opacity = 0; self.ids.inp_recuperar_s.disabled = True
        self.ids.box_btn_recuperar.size_hint_y = 0.2
        self.ids.btn_recuperar.accion = self.Volver_Login
        self.ids.btn_recuperar.text = 'Login'

    def Volver_Login(self):
        self.abrir_otra_pantalla('AA_Login', transition=SlideTransition(direction="right"))
        Clock.schedule_once(lambda dt: self.Ingresar_Correo_o_Telefono(), 1)

    def Regresar_Login(self):
        self.abrir_otra_pantalla("AA_Login", SlideTransition(direction="right"))
        Clock.schedule_once(lambda dt: self.Ingresar_Correo_o_Telefono(), 0.5)