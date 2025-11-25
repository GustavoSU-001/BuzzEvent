from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition

from Modulos.Singleton.Perfil import Singleton_Perfil
import uuid



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
        self.Abrir_Menu('perfil', Rut)
        
    def Abrir_Menu(self, perfil, Rut):
        #Singleton_Perfil.get_instance().rut=rut
        #Singleton_Perfil.get_instance().tipo_perfil=perfil
        
        self.perfil=Rut
        if Rut == "Estandar":
            self.abrir_otra_pantalla("BA_Estandar",transition= SlideTransition(direction="up"))
        if Rut == "Organizador":
            self.abrir_otra_pantalla("BB_Organizador",transition= SlideTransition(direction="up"))
        if Rut == "Administrador":
            self.abrir_otra_pantalla("BC_Administrador",transition= SlideTransition(direction="up"))
    
    def Abrir_Ventana(self):
        rol=Singleton_Perfil.get_instance()
        codigo_unico=uuid.uuid4().hex
        rol.tipo_perfil=None
        rol.rut='22.222.222-2'
        rol.token=codigo_unico
        
    
    def Cerrar_Ventana(self):
        rol=Singleton_Perfil.get_instance()
        rol.tipo_perfil=self.perfil
        
