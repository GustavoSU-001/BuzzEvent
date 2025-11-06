from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition



class Layout_Estandar(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Estandar,self).__init__(**kwargs)
        self.abrir_otra_pantalla= abrir_otra_pantalla
        
    def Abrir_Mapa(self):
        self.abrir_otra_pantalla("BAA_Mapa", transition= SlideTransition(direction="left"))
