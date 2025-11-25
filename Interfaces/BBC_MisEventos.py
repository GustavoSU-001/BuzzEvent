from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from Modulos.Singleton.Perfil import Singleton_Perfil
from Modulos.Singleton.Eventos import Singleton_Evento

from kivy.factory import Factory
from Modulos.BaseDatos.Conexion import Lectura_Eventos_DB




class Layout_MisEventos(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_MisEventos,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        self.id_evento=''
        Singleton_Evento()

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
            lect = Lectura_Eventos_DB()
            info = lect.obtener_informacion(perfil)
            #self.Imagenes = info[self.id_evento]['Imagenes']
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
            print(e)
        
    
    def Abrir_Ventana(self):
        self.id_evento=''
        self.Cargar_Eventos()
        
    def Cerrar_Ventana(self):
        print('----------------------------')
        print(self.id_evento)
        Singleton_Evento.get_instance().id_evento=self.id_evento
        print(Singleton_Evento.get_instance().id_evento)
        print('----------------------------')
        











