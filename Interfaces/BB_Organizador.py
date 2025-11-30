from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import SlideTransition
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from Modulos.Singleton.Perfil import Singleton_Perfil


class Menu_Cuenta(ModalView):
    login = ObjectProperty(None)



class Layout_Organizador(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Organizador,self).__init__(**kwargs)
        self.abrir_otra_pantalla= abrir_otra_pantalla
        #Clock.schedule_once(self.actualizar_datos_perfil, 0.1)
    

    
        
    def Abrir_Mapa(self):
        self.abrir_otra_pantalla("BAA_Mapa", transition= SlideTransition(direction="left"))
        
    def Abrir_CreacionEventos(self):
        self.abrir_otra_pantalla("BBB_CreacionEventos", transition= SlideTransition(direction="left"))
        
    def Abrir_MisEventos(self):    
        self.abrir_otra_pantalla("BBC_MisEventos", transition= SlideTransition(direction="left"))
        
    def Abrir_Estadisticas(self):
        self.abrir_otra_pantalla("BBD_Estadisticas", transition= SlideTransition(direction="left"))
        
    def Abrir_Cupones(self):
        self.abrir_otra_pantalla("BAC_Cupones", transition= SlideTransition(direction="right"))
        
    def Abrir_Suscripciones(self):
        self.abrir_otra_pantalla("BAD_Suscripciones", transition= SlideTransition(direction="right"))
        
    def Abrir_Login(self):
        self.abrir_otra_pantalla("AA_Login", transition= SlideTransition(direction="right"))

    def Abrir_menu_Cuenta(self):
        mv=ModalView()
        
    
    def Abrir_Ventana(self):
        rol=Singleton_Perfil.tipo_perfil
        if rol != "Organizador":
            self.Abrir_Login()
        
    # def actualizar_datos_perfil(self, dt):
    #         """
    #         Busca los datos guardados en la sesión (Singleton) 
    #         y los escribe en el botón de la interfaz.
    #         """
    #         try:
    #             # 1. Obtenemos la instancia de la sesión
    #             perfil = Singleton_Perfil.get_instance()
                
    #             # 2. Obtenemos nombre y apellido (con valores por defecto si están vacíos)
    #             nombre_real = getattr(perfil, 'nombre', '')
    #             apellido_real = getattr(perfil, 'apellido', '')
                
    #             print(f"DEBUG: Cargando perfil en Organizador: {nombre_real} {apellido_real}")

    #             # 3. Buscamos el botón por su ID y actualizamos su propiedad TEXT
    #             if 'btn_cuenta_usuario' in self.ids:
    #                 boton = self.ids.btn_cuenta_usuario
    #                 # ESTA ES LA LÍNEA QUE HACE QUE SE VEA EN PANTALLA:
    #                 boton.text = f"{nombre_real} {apellido_real}"
                    
    #         except Exception as e:
    #             print(f"Error actualizando datos del organizador: {e}")
        
