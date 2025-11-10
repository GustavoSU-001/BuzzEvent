import requests
import json
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.popup import Popup #Para mostrar errores
from kivy.uix.label import Label #label para el popup
from kivy.clock import Clock
from functools import partial
#ID del proyecto de Firebase
PROJECT_ID = "eva3-72fb2"

# Esta es la URL de la API REST de Firestore.
FIRESTORE_API_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"

#    rut validacion function    
def validar_rut(rut_completo):
    """
    Valida que un RUT chileno sea matemáticamente correcto.
    """
    try:
        # 1. Limpiar el RUT de puntos, guiones y pasarlo a mayúsculas
        rut_limpio = rut_completo.upper().replace(".", "").replace("-", "")
        
        if len(rut_limpio) < 2:
            return False # No puede ser tan corto

        # 2. Separar cuerpo y dígito verificador
        cuerpo_str = rut_limpio[:-1]
        #cuerpo_int = int(cuerpo_str) # Asegura que el cuerpo sea numérico
        verificador = rut_limpio[-1]

        # 3. Calcular el dígito verificador esperado (Algoritmo Módulo 11)
        suma = 0
        multiplicador = 2

        # 4. Iterar sobre el cuerpo al revés
        for digito in reversed(cuerpo_str):
            suma += int(digito) * multiplicador
            multiplicador += 1
            if multiplicador == 8:
                multiplicador = 2 # Reiniciar el multiplicador
        
        # 5. Calcular el resto
        resto = suma % 11
        
        # 6. Obtener el dígito esperado
        digito_esperado_num = 11 - resto
        
        # 7. Manejar casos especiales
        if digito_esperado_num == 11:
            digito_esperado = '0'
        elif digito_esperado_num == 10:
            digito_esperado = 'K'
        else:
            digito_esperado = str(digito_esperado_num)
            
        # 8. Comparar el verificador ingresado con el calculado
        return verificador == digito_esperado

    except ValueError:
        # Si algo falla (ej. letras en el cuerpo), no es válido
        return False
    except Exception as e:
        print(f"Error inesperado al validar RUT: {e}")
        return False
# --- FIN DE LA FUNCIÓN DE VALIDACIÓN ---


#################################################################################

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
        
#################################################################################




class Layout_Registrar_L(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Registrar_L,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla

        ##############################BLOQUEO################################################## 
        Clock.schedule_once(self._bind_inputs)  # Limpiar campos al iniciar la pantalla
        
        _color_original_texto_edad = (1, 1, 1, 1) # Un color por defecto (blanco)
        self._telefono_blocker = False
        self._alias_blocker = False

    def _bind_inputs(self,dt):
        try:
            # -------------------- RUT --------------------------------------------
            rut_input_widget = self.ids.rut_input.ids.usuario
            rut_input_widget.bind(focus=self.validar_y_formatear_rut)
            funcion_limite_rut = partial(self.limitar_caracteres, 12)
            rut_input_widget.bind(text=funcion_limite_rut)

            #--- FIN DEL RUT --------------------------------------------------

                    # --- MODIFICACIÓN PARA 'NOMBRES' ---
            nombres_input_widget = self.ids.nombres_input.ids.usuario
           #limitador de caracteres a 50
            funcion_limite_nombres = partial(self.limitar_caracteres, 50)
            nombres_input_widget.bind(text=funcion_limite_nombres)
            #al salir del input este hace el
            nombres_input_widget.bind(focus=self.capitalizar_al_salir) 
                    # --- FIN DE MODIFICACIÓN ---

                    # --- MODIFICACIÓN PARA 'Apellido' ---
            nombres_input_widget = self.ids.apellidos_input.ids.usuario
           #limitador de caracteres a 50
            funcion_limite_apellidos = partial(self.limitar_caracteres, 50)
            nombres_input_widget.bind(text=funcion_limite_apellidos)
            #al salir del input este hace el
            nombres_input_widget.bind(focus=self.capitalizar_al_salir) 
                    # --- FIN DE MODIFICACIÓN ---

            # --------------------------EDAD------------------------------------
# 1. Obtenemos el widget
            edad_widget = self.ids.edad_input.ids.usuario
        
        # Creamos la función con 'partial' (como en tu código)
            funcion_limite_edad = partial(self.limitar_caracteres, 3)
        
        #  La vinculamos al evento 'text'
            edad_widget.bind(text=funcion_limite_edad)

        # --- Vinculación de la Validación de Rango ---
            edad_widget.bind(focus=self.validar_edad_rango)
        # para poner numeros
            edad_widget.input_filter = self.filtro_solo_digitos
        # Guardamos el color original del texto si esta correcto o no 
            self._color_original_texto_edad = edad_widget.foreground_color

                            #2. Proteccion del prefijo del telefono
            telefono_widget = self.ids.telefono_input.ids.usuario
            telefono_widget.text = "+56"  # Establecer el prefijo inicial   
            telefono_widget.bind(text=self.proteger_prefijo_telefono)
            funcion_limite_telefono = partial(self.limitar_caracteres, 12) # +56 más 9 dígitos
            telefono_widget.bind(text=funcion_limite_telefono)
            telefono_widget.input_filter = self.filtro_solo_digitos

                        # --- FIN DE LA PROTECCIÓN DEL PREFIJO ---

                        #3. Formateo del alias sin espacios
            
            alias_widget = self.ids.alias_input.ids.usuario
            alias_widget.input_filter = self.filtro_sin_espacios
            funcion_limite_telefono= partial(self.limitar_caracteres,15) # Limitar a 15 caracteres
            alias_widget.bind(text=funcion_limite_telefono)
                        # --- FIN DEL FORMATEO ---

        #4. Validacion del correo
            correo_widget = self.ids.correo_input.ids.usuario
            correo_widget.bind(focus=self.validar_formato_correo)
            # --------------------------------------------------------------------------------

        # -------------------- CONTRASEÑA------------------------------------------------------------
        #5. Validacion de la fuerza de la contrasena
            # --- AÑADE ESTA VINCULACIÓN PARA LA CONTRASEÑA ---
            contrasena_widget = self.ids.contrasena_input.ids.usuario
            contrasena_widget.bind(focus=self.validar_fuerza_contrasena)
            # --------------------------------------------------

        except AttributeError as e:
            print(f"Error al enlazar el RUT: {e}. Asegúrate de que el ID en el .kv coincida.")

        ################################################################################
    # --- FILTRO Para digitos en la edad ---

    def filtro_solo_digitos(self, substring, from_undo):
        # Esta función revisará cada caracter
        # y solo devolverá aquellos que sean un número.
        return "".join(c for c in substring if c.isdigit())

    # --- FIN DEL FILTRO ---
    
    ######################VALIDACION DEL RANGO DE EDAD#############################################################
    def validar_edad_rango(self, text_input_widget, is_focused):
        
        COLOR_ERROR = (1, 0, 0, 1)  # Rojo
        COLOR_CORRECTO = (0, 1, 0, 1)  # Verde

        if is_focused:
            # El usuario HIZO CLIC: restaurar color normal
            text_input_widget.foreground_color = self._color_original_texto_edad
            return

        # El usuario SALIÓ: validar
        texto_edad = text_input_widget.text
        
        if not texto_edad:
            text_input_widget.foreground_color = self._color_original_texto_edad
            return

        try:
            edad = int(texto_edad)
            if 18 <= edad <= 100:
                # Correcto
                text_input_widget.foreground_color = COLOR_CORRECTO
            else:
                # Error: fuera de rango
                text_input_widget.foreground_color = COLOR_ERROR
        except ValueError:
            text_input_widget.foreground_color = COLOR_ERROR
    ####################################################################################

    ################################################################################
        # --- NUEVA FUNCIÓN PARA LIMITAR CARACTERES ---
    def limitar_caracteres(self,max_chars, text_input_widget, texto_actual):
        """
        Esta función se llama cada vez que el texto de un input cambia.
        Trunca el texto si excede 'max_chars'.
        """
        if len(texto_actual) > max_chars:
            cursor_pos_original = text_input_widget.cursor_col
            # Corta el texto al límite máximo
            text_input_widget.text = texto_actual[:max_chars]
            # Ajusta el cursor para que no quede fuera de rango
            text_input_widget.cursor = (min(cursor_pos_original, max_chars), 0)
    # --- FIN DE LA NUEVA FUNCIÓN ---       
    

#### creo eque este me esta limitando la verificaion del rut 


    def formatear_on_rut_text(self, text_input_widget, texto_actual):
        cursor_pos_original = text_input_widget.cursor_col
        rut_limpio = texto_actual.replace(".", "").replace("-", "").upper()
        if not rut_limpio:
            text_input_widget.text = ""
            return
        try:
            verificador = rut_limpio[-1]
            cuerpo_str = rut_limpio[:-1]

            if cuerpo_str:
                cuerpo_int = int(cuerpo_str)
                cuerpo_formateado = f"{cuerpo_int:,}".replace(",", ".")
                texto_final = f"{cuerpo_formateado}-{verificador}"
            else:
                texto_final = verificador
        except ValueError:
            texto_final = texto_actual
            return
        if texto_actual==texto_final:
            return
        text_input_widget.text = texto_final
        diff = len(texto_final) - len(texto_actual)
        text_input_widget.cursor = (max(0, cursor_pos_original + diff), 0)


    ################################################################################
    # --- la palabra empieza con mayuscula' (MÁS SENCILLA) ---
    def capitalizar_al_salir(self, text_input_widget, focus):
        """
        Funcion que me cambia de juan a Juan al salir del input 
        """
        # Solo actuar cuando el usuario SALE del campo (focus=False)
        if not focus:
            texto_actual = text_input_widget.text
            texto_capitalizado = texto_actual.title()
            # Actualiza el texto solo si es necesario
            if texto_actual != texto_capitalizado:
                text_input_widget.text = texto_capitalizado
    # --- ---

    ################################################################################



    # mensajes emergentes
    ################################################################################
    def mostrar_popup(self, titulo, mensaje):   #funcion para mostrar popups y reutilizable
        popup = Popup(
            title=titulo,
            content=Label(text=mensaje),
            size_hint=(None, None), size=(400, 200)
        )
        popup.open()
    
    def Regresar_Login(self):  #funcion para regresar a la pantalla de login
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
        
        #cuando el rut no es valido
        if not validar_rut(rut):
            self.mostrar_popup("Error de Registro", "El RUT ingresado no es válido.")
            return  # Detenemos la función si el RUT no es válido
        
        # Verificar el rango de edad
        try:
            edad_numero=int(edad_texto)
            if edad_numero < 18 or edad_numero > 100:
                self.mostrar_popup("Error de Registro", "La edad debe estar entre 18 y 100 años.")
                return  # Detenemos la función si la edad está fuera de rango
        except ValueError:
            self.mostrar_popup("Error de Registro", "La edad debe ser un número válido.")
            return  # Detenemos la función si la edad no es un número válido
        
        #verificar correo valido
        dominion_permitidos = ['@gmail.com', '@hotmail.com', '@inacapmail.cl']
        correo_limpio=correo.strip().lower()
        es_valido=False
        for dominio in dominion_permitidos:
            if correo_limpio.endswith(dominio):
                es_valido=True
                break
        #para ver si el dominio es valido y tenga texto antes
        if not es_valido or not correo_limpio.split('@')[0]:
            self.mostrar_popup("Error de Registro", "El correo electrónico no tiene un formato válido.")
            return  # Detenemos la función si el correo no es válido
        
        # Verificacion contraña fuerte
        min_longitud = 8
        tiene_numero = any(c.isdigit() for c in contrasena)
        tiene_mayuscula = any(c.isupper() for c in contrasena)
        tiene_minuscula = any(c.islower() for c in contrasena)
        caracteres_especiales = any(c in self.CARACTERES_ESPECIALES for c in contrasena)

        es_contrasena_valida =(
            len(contrasena) >= min_longitud and
            tiene_numero and
            tiene_mayuscula and
            tiene_minuscula and
            caracteres_especiales)
        if not es_contrasena_valida:
            self.mostrar_popup("Error de Registro", "La contraseña no cumple con los requisitos.")
            return  # Detenemos la función si la contraseña no es válida
                                    

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


    ################################################################################
    # --- FUNCIÓN DE PROTECCIÓN DEL PREFIJO DEL TELÉFONO ---

    def proteger_prefijo_telefono(self, text_input_widget, texto_actual):
            prefijo = "+56"
        
        # 1. Revisar el bloqueador
            if self._telefono_blocker:
                return
            self._telefono_blocker = True # Activar bloqueador
        
        # 2. Lógica de protección
        # Si el texto ya no empieza con "+56" o es más corto...
            if not texto_actual.startswith(prefijo) or len(texto_actual) < len(prefijo):
            
            # ...lo forzamos a ser "+56"
                text_input_widget.text = prefijo
            
            # Y movemos el cursor (la barrita) al final del prefijo
                text_input_widget.cursor = (len(prefijo), 0)

        # 3. Desactivar el bloqueador
            self._telefono_blocker = False

    ################################################################################
    def formatear_alias_sin_espacios(self, text_input_widget, texto_actual):
        """
        Esta función elimina los espacios del texto del alias
        en tiempo real.
        """
        # 1. Revisar el bloqueador
        if self._alias_blocker:
            return
        
        # 2. Activar el bloqueador
        self._alias_blocker = True
        
        # 3. Guardar posición del cursor
        cursor_pos_original = text_input_widget.cursor_col
        
        # 4. Lógica: reemplazar espacios
        texto_sin_espacios = texto_actual.replace(" ", "")
        
        # 5. Comprobar si hubo un cambio
        if texto_actual != texto_sin_espacios:
            # 6. Aplicar el texto nuevo
            text_input_widget.text = texto_sin_espacios
            
            # 7. Ajustar el cursor
            # (Calcula la diferencia, que será negativa, y ajusta)
            diff = len(texto_sin_espacios) - len(texto_actual)
            nueva_pos = max(0, cursor_pos_original + diff)
            text_input_widget.cursor = (nueva_pos, 0)

        # 8. Desactivar el bloqueador
    def filtro_sin_espacios(self, substring, from_undo):
        # Esta función rechaza el carácter si es un espacio
        if " " in substring:
            return "" # Devuelve vacío (rechaza el espacio)
        return substring # Acepta todos los demás caracteres
    
    def validar_formato_correo(self, text_input_widget, is_focused):
        """
        Valida que el correo termine con los dominios permitidos
        cuando el usuario sale del campo.
        """
        COLOR_ERROR = (1, 0, 0, 1)  # Rojo
        COLOR_CORRECTO = (0, 1, 0, 1)  # Verde
        
        # 1. Al ENTRAR al campo (is_focused = True)
        if is_focused:
            # Restauramos el color original del texto (usamos la misma variable de la edad)
            text_input_widget.foreground_color = self._color_original_texto_edad
            return

        # 2. Al SALIR del campo (is_focused = False)
        
        # Obtenemos el texto y lo "limpiamos" (minúsculas y sin espacios extra)
        texto_correo = text_input_widget.text.strip().lower()

        # Si el campo está vacío, lo dejamos con el color normal
        if not texto_correo:
            text_input_widget.foreground_color = self._color_original_texto_edad
            return

        # --- Lógica de Validación ---
        dominios_permitidos = [
            "@gmail.com",
            "@hotmail.com",
            "@inacapmail.cl"
        ]
        
        es_valido = False
        
        # Primero, revisamos si termina con un dominio válido
        for dominio in dominios_permitidos:
            if texto_correo.endswith(dominio):
                es_valido = True
                break
        
        # Segundo, revisamos que haya algo ANTES del @
        if es_valido:
            partes = texto_correo.split('@')
            # Debe tener exactamente 2 partes (local@dominio)
            # y la parte 'local' (partes[0]) no debe estar vacía
            if len(partes) != 2 or not partes[0]:
                es_valido = False
        
        # 3. Aplicar el color según la validación
        if es_valido:
            # ¡Correcto!
            text_input_widget.foreground_color = COLOR_CORRECTO
        else:
            # ¡Error!
            text_input_widget.foreground_color = COLOR_ERROR


    ################################################################################
    # --- FUNCIÓN DE VALIDACIÓN DE FUERZA DE CONTRASEÑA --- 
    
    # Define los caracteres especiales que aceptarás
    CARACTERES_ESPECIALES = set("!@#$%^&*()_+-=[]{}|;:'\",.<>/?")

    # ... (tu __init__, setup_bindings, etc.) ...
    
    def validar_fuerza_contrasena(self, text_input_widget, is_focused):
        """
        Valida la seguridad de la contraseña al salir del campo.
        Reglas:
        1. Mínimo 8 caracteres.
        2. Al menos una mayúscula.
        3. Al menos una minúscula.
        4. Al menos un número.
        5. Al menos un carácter especial.
        """
        COLOR_ERROR = (1, 0, 0, 1)  # Rojo
        COLOR_CORRECTO = (0, 1, 0, 1)  # Verde

        # 1. Al ENTRAR al campo (is_focused = True)
        if is_focused:
            # Restauramos el color original
            text_input_widget.foreground_color = self._color_original_texto_edad
            return

        # 2. Al SALIR del campo (is_focused = False)
        password = text_input_widget.text

        # Si el campo está vacío, no es un error de formato.
        # Lo dejamos pasar (la función 'registrar_usuario_firestore' 
        # ya comprueba si los campos están vacíos).
        if not password:
            text_input_widget.foreground_color = self._color_original_texto_edad
            return

        # --- Lógica de Validación ---
        min_longitud = 8
        tiene_numero = any(c.isdigit() for c in password)
        tiene_mayuscula = any(c.isupper() for c in password)
        tiene_minuscula = any(c.islower() for c in password)
        tiene_especial = any(c in self.CARACTERES_ESPECIALES for c in password)
        
        # Comprobamos todas las reglas
        es_valida = (
            len(password) >= min_longitud and
            tiene_numero and
            tiene_mayuscula and
            tiene_minuscula and
            tiene_especial
        )

        # 3. Aplicar el color
        if es_valida:
            text_input_widget.foreground_color = COLOR_CORRECTO
        else:
            text_input_widget.foreground_color = COLOR_ERROR

        # --- FIN DE LA FUNCIÓN DE VALIDACIÓN ---

    ################################################################################
                    #  RUT VALIDACION   
    def validar_y_formatear_rut(self, text_input_widget, is_focused):
        """
        Formatea y Valida el RUT cuando el usuario sale del campo.
        """
        COLOR_ERROR = (1, 0, 0, 1)  # Rojo
        COLOR_CORRECTO = (0, 1, 0, 1)  # Verde
        
        # 1. --- AL ENTRAR AL CAMPO (is_focused = True) ---
        if is_focused:
            # Restauramos el color del texto al original
            text_input_widget.foreground_color = self._color_original_texto_edad
            
            # Quitamos puntos y guion para que el usuario edite el número limpio
            texto_actual = text_input_widget.text
            rut_limpio = texto_actual.replace(".", "").replace("-", "").upper()
            
            if texto_actual != rut_limpio:
                text_input_widget.text = rut_limpio
            return

        # 2. --- AL SALIR DEL CAMPO (is_focused = False) ---
        texto_actual = text_input_widget.text
        
        # Si está vacío, no hacemos nada
        if not texto_actual:
            return

        # 3. --- Validamos usando TU función global 'validar_rut' ---
        if validar_rut(texto_actual):
            # Es VÁLIDO: le ponemos el formato
            
            rut_limpio = texto_actual.replace(".", "").replace("-", "").upper()
            try:
                verificador = rut_limpio[-1]
                cuerpo_str = rut_limpio[:-1]
                
                # Formato de miles (ej: 12.345.678)
                cuerpo_formateado = f"{int(cuerpo_str):,}".replace(",", ".")
                
                texto_final = f"{cuerpo_formateado}-{verificador}"
                text_input_widget.text = texto_final
                text_input_widget.foreground_color = COLOR_CORRECTO
            except Exception:
                # Si falla el formato (raro si 'validar_rut' pasó),
                # simplemente dejamos el texto limpio.
                text_input_widget.text = rut_limpio
        
        else:
            # Es INVÁLIDO: ponemos el texto rojo
            text_input_widget.foreground_color = COLOR_ERROR
                # --- FIN DE LA FUNCIÓN DE VALIDACIÓN ---