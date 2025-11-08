
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition





class Layout_EventosFavoritos(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_EventosFavoritos,self).__init__(**kwargs)
        self.abrir_otra_pantalla= abrir_otra_pantalla
        
    def Regresar_MenuPrincipal(self, rol):
        if rol == "Estandar":
            self.abrir_otra_pantalla("BA_Estandar",transition= SlideTransition(direction="right"))
        elif rol == "Organizador":
            self.abrir_otra_pantalla("BB_Organizador",transition= SlideTransition(direction="right"))
        elif rol == "Administrador":
            self.abrir_otra_pantalla("BC_Administrador",transition= SlideTransition(direction="right"))
        else:
            self.abrir_otra_pantalla("AA_Login",transition= SlideTransition(direction="right"))
            
            




