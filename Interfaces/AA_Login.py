from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition




class Layout_Login(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Login,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        
    def Boton_recuperar_contrasena(self):
        self.abrir_otra_pantalla("ABA_Recuperar_L",transition= SlideTransition(direction="left"))
        
    def Boton_registrar_cuenta(self):
        self.abrir_otra_pantalla("ACA_Registrar_L",transition= SlideTransition(direction="left"))

    def Iniciar_Sesion(self, Rut, Contraseña=None):
        if  self.root.ids.username_input.text == "usuario" or self.root.ids.password_input.text == "123":
            return  # Aquí podrías mostrar un mensaje de error al usuario
        if Rut == "Estandar":
            self.abrir_otra_pantalla("BA_Estandar",transition= SlideTransition(direction="up"))
        if Rut == "Organizador":
            self.abrir_otra_pantalla("BB_Organizador",transition= SlideTransition(direction="up"))
        if Rut == "Administrador":
            self.abrir_otra_pantalla("BC_Administrador",transition= SlideTransition(direction="up"))
        
