from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from Modulos.Singleton.Perfil import Singleton_Perfil
from Modulos.Singleton.Eventos import Singleton_Evento

from kivy.factory import Factory
from Modulos.BaseDatos.Conexion import Lectura_Eventos_DB




from kivy.properties import BooleanProperty

from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty

class Input_Filter_Date(TextInput):
    letras_permitido = StringProperty('0123456789')
    
    def __init__(self, **kwargs):
        super(Input_Filter_Date, self).__init__(**kwargs)
        self.multiline = False
        self.bind(focus=self.on_focus)
        self.bind(text=self.filtrar_caracteres)

    def on_focus(self, instance, value):
        if value:
            # Ganó foco: Quitar formato (mostrar solo números)
            texto_limpio = "".join([c for c in instance.text if c in self.letras_permitido])
            instance.unbind(text=self.filtrar_caracteres)
            instance.text = texto_limpio
            instance.bind(text=self.filtrar_caracteres)
        else:
            # Perdió foco: Aplicar formato DD-MM-YYYY
            self.aplicar_formato(instance)

    def aplicar_formato(self, instance):
        value = instance.text
        caracteres_puros = [char for char in value if char in self.letras_permitido]
        
        # Si no hay suficientes caracteres, no formatear o dejar como está
        if not caracteres_puros:
            return

        # Formatear DD-MM-YYYY
        texto_unido = "".join(caracteres_puros)
        nuevo_texto = []
        
        # DD
        if len(texto_unido) >= 2:
            nuevo_texto.append(texto_unido[:2])
            nuevo_texto.append('-')
            # MM
            if len(texto_unido) >= 4:
                nuevo_texto.append(texto_unido[2:4])
                nuevo_texto.append('-')
                # YYYY
                nuevo_texto.append(texto_unido[4:8])
            else:
                nuevo_texto.append(texto_unido[2:])
        else:
            nuevo_texto.append(texto_unido)
            
        texto_final = "".join(nuevo_texto)
        
        instance.unbind(text=self.filtrar_caracteres)
        instance.text = texto_final
        instance.bind(text=self.filtrar_caracteres)

    def filtrar_caracteres(self, instance, value):
        if not value:
            return

        if instance.focus:
            # Solo permitir números y limitar longitud (8 dígitos para DDMMAAAA)
            caracteres_puros = "".join([char for char in value if char in self.letras_permitido])
            texto_final = caracteres_puros[:8]
            
            if value != texto_final:
                instance.unbind(text=self.filtrar_caracteres)
                instance.text = texto_final
                instance.bind(text=self.filtrar_caracteres)


class Layout_MisEventos(BoxLayout):
    show_dates = BooleanProperty(False)

    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_MisEventos,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        self.id_evento=''
        Singleton_Evento()

    def toggle_dates(self):
        self.show_dates = not self.show_dates

    def Abrir_MenuPrincipal(self):
        rol = Singleton_Perfil.get_instance().tipo_perfil
        if rol == 'Estandar':
            self.abrir_otra_pantalla("BA_Estandar", transition=SlideTransition(direction="up"))
        elif rol == 'Organizador':
            self.abrir_otra_pantalla("BB_Organizador", transition=SlideTransition(direction="up"))
        elif rol == 'Administrador':
            self.abrir_otra_pantalla("BC_Administrador", transition=SlideTransition(direction="up"))
        else:
            self.abrir_otra_pantalla("AA_Login", transition=SlideTransition(direction="up"))
    
    def Abrir_Login(self):
        self.abrir_otra_pantalla("AA_Login", transition= SlideTransition(direction="right"))
            
    def Abrir_InterfazEvento(self,id_evento,*args):
        print("Cambiando de interfaz")
        rol = Singleton_Perfil.get_instance().tipo_perfil
        self.id_evento=id_evento
        print(id_evento)
        Singleton_Evento.get_instance().id_evento=self.id_evento
        
        if rol == 'Organizador':
            self.abrir_otra_pantalla("BBCA_InterfazEvento", transition=SlideTransition(direction="right"))
        else:
            self.abrir_otra_pantalla("AA_Login", transition=SlideTransition(direction="right"))
    
    
    def Cargar_Eventos(self):
        self.ids.Lista_MisEventos.clear_widgets()
        try:
            perfil = Singleton_Perfil.get_instance().rut
            
            # Obtener valores de los filtros
            etiquetas_text = self.ids.filtro_etiquetas.text
            fecha_inicio_text = self.ids.filtro_fecha_inicio.text
            fecha_fin_text = self.ids.filtro_fecha_fin.text
            
            # Procesar etiquetas (separar por comas y limpiar espacios)
            etiquetas = [e.strip() for e in etiquetas_text.split(',')] if etiquetas_text else None
            
            # Procesar fechas (convertir a datetime si es necesario, o pasar string y que el backend maneje)
            # El backend espera datetime objects para comparaciones robustas
            from datetime import datetime
            fecha_inicio = None
            fecha_fin = None
            
            if fecha_inicio_text:
                try:
                    fecha_inicio = datetime.strptime(fecha_inicio_text, "%d-%m-%Y")
                except ValueError:
                    print("Formato de fecha inicio inválido")
            
            if fecha_fin_text:
                try:
                    fecha_fin = datetime.strptime(fecha_fin_text, "%d-%m-%Y")
                except ValueError:
                    print("Formato de fecha fin inválido")

            lect = Lectura_Eventos_DB()
            # Pasar filtros a obtener_informacion
            info = lect.obtener_informacion(organizador=perfil, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, etiquetas=etiquetas)
            
            llaves = list(info.keys())
            for l in llaves:
                ev=Factory.Elementos_MisEventos()
                ev.id = l
                ev.titulo= info[l]['Titulo']
                ev.estado= info[l]['Estado']
                ev.ubicacion = info[l]['Ubicacion']
                ev.on_press = lambda event_id=l: self.Abrir_InterfazEvento(event_id)
                self.ids.Lista_MisEventos.add_widget(ev)
        except Exception as e:
            print(f"Error cargando eventos: {e}")
        
    
    def Abrir_Ventana(self):
        self.id_evento=''
        self.Cargar_Eventos()
        
    def Cerrar_Ventana(self):
        print('----------------------------')
        print(self.id_evento)
        Singleton_Evento.get_instance().id_evento=self.id_evento
        print(Singleton_Evento.get_instance().id_evento)
        print('----------------------------')
        











