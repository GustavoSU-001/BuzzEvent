from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition

from Modulos.Singleton.Perfil import Singleton_Perfil




class Layout_Login(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Login,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        rol=Singleton_Perfil().get_instance()
        print(rol.tipo_perfil)
        self.perfil = None
        rol.tipo_perfil=None
        print(rol.tipo_perfil)
        
    def Boton_recuperar_contrasena(self):
        self.abrir_otra_pantalla("ABA_Recuperar_L",transition= SlideTransition(direction="left"))
        
    def Boton_registrar_cuenta(self):
        self.abrir_otra_pantalla("ACA_Registrar_L",transition= SlideTransition(direction="left"))

    def Iniciar_Sesion(self, Rut, Contraseña=None):
        #if  self.root.ids.username_input.text == "usuario":
        #    return  # Aquí podrías mostrar un mensaje de error al usuario
        self.perfil=Rut
        if Rut == "Estandar":
            self.abrir_otra_pantalla("BA_Estandar",transition= SlideTransition(direction="up"))
        if Rut == "Organizador":
            self.abrir_otra_pantalla("BB_Organizador",transition= SlideTransition(direction="up"))
        if Rut == "Administrador":
            self.abrir_otra_pantalla("BC_Administrador",transition= SlideTransition(direction="up"))
    
    def Abrir_Ventana(self):
        rol=Singleton_Perfil.get_instance()
        print(rol.tipo_perfil)
        self.perfil = None
        rol.tipo_perfil=None
        print(rol.tipo_perfil)
        
    
    def Cerrar_Ventana(self):
        rol=Singleton_Perfil.get_instance()
        print(rol.tipo_perfil)
        rol.tipo_perfil=self.perfil
        print(rol.tipo_perfil)
        
