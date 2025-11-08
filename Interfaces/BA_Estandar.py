from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
from kivy.properties import ObjectProperty

from Modulos.Singleton.Perfil import Singleton_Perfil


class Menu_Cuenta(ModalView):
    login = ObjectProperty(None)

class Layout_Estandar(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Estandar,self).__init__(**kwargs)
        self.abrir_otra_pantalla= abrir_otra_pantalla
        
        
        
    def Abrir_Mapa(self):
        self.abrir_otra_pantalla("BAA_Mapa", transition= SlideTransition(direction="left"))
        
    def Abrir_EventosFavoritos(self):
        self.abrir_otra_pantalla("BAB_EventosFavoritos", transition= SlideTransition(direction="left"))
        
    def Abrir_Login(self):
        self.abrir_otra_pantalla("AA_Login", transition= SlideTransition(direction="right"))

    def Abrir_menu_Cuenta(self):
        mv=ModalView()
        
    def Abrir_Ventana(self):
        rol=Singleton_Perfil.tipo_perfil
        if rol != "Estandar":
            self.Abrir_Login()
            
        
        




