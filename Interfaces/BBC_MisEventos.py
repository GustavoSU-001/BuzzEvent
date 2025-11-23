from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from Modulos.Singleton.Perfil import Singleton_Perfil






class Layout_MisEventos(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_MisEventos,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla

    def Abrir_MenuPrincipal(self):
        rol = Singleton_Perfil.get_instance().tipo_perfil
        if rol == 'Estandar':
            self.abrir_otra_pantalla("BA_Estandar", transition=SlideTransition(direction="right"))
        elif rol == 'Organizador':
            self.abrir_otra_pantalla("BB_Organizador", transition=SlideTransition(direction="right"))
        elif rol == 'Administrador':
            self.abrir_otra_pantalla("BC_Administrador", transition=SlideTransition(direction="right"))
        else:
            self.abrir_otra_pantalla("AA_Login", transition=SlideTransition(direction="right"))












