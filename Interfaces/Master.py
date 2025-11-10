
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

from kivy.uix.screenmanager import NoTransition

from Interfaces.AA_Login import Layout_Login
from Interfaces.ABA_Recuperar_L import Layout_Recuperar_L
from Interfaces.ACA_Registrar_L import Layout_Registrar_L

from Interfaces.BA_Estandar import Layout_Estandar
from Interfaces.BAA_Mapa import Layout_Mapa
from Interfaces.BAB_EventosFavoritos import Layout_EventosFavoritos 
from Interfaces.BAC_Cupones import Layout_Cupones
from Interfaces.BAD_Suscripciones import Layout_Suscripciones

from Interfaces.BB_Organizador import Layout_Organizador
from Interfaces.BBB_CreacionEventos import Layout_CreacionEventos

from Interfaces.BC_Administrador import Layout_Administrador



class AA_Screen(Screen):
    def __init__(self, **kwargs):
        super(AA_Screen,self).__init__(**kwargs)
        self.layout= Layout_Login(self.abrir_otra_pantalla)
        self.add_widget(self.layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla
       
    def on_pre_enter(self, *args):
        if hasattr(self.layout, 'Abrir_Ventana'):
            self.layout.Abrir_Ventana()
            
    def on_pre_leave(self, *args):
        if hasattr(self.layout, 'Cerrar_Ventana'):
            self.layout.Cerrar_Ventana()
            
        
class AB_Screen(Screen):
    def __init__(self, **kwargs):
        super(AB_Screen,self).__init__(**kwargs)
        layout= Layout_Recuperar_L(self.abrir_otra_pantalla)
        self.add_widget(layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla
        

class AC_Screen(Screen):
    def __init__(self, **kwargs):
        super(AC_Screen,self).__init__(**kwargs)
        layout= Layout_Registrar_L(self.abrir_otra_pantalla)
        self.add_widget(layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BA_Screen(Screen):
    def __init__(self, **kwargs):
        super(BA_Screen,self).__init__(**kwargs)
        layout= Layout_Estandar(self.abrir_otra_pantalla)
        self.add_widget(layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BAA_Screen(Screen):
    def __init__(self, **kwargs):
        super(BAA_Screen,self).__init__(**kwargs)
        self.layout= Layout_Mapa(self.abrir_otra_pantalla)
        self.add_widget(self.layout)
        
    #Enciende todas las funciones del mapa al entrar en la ventana
    def on_pre_enter(self, *args):
        if hasattr(self.layout, 'Iniciar_Ventana'):
            self.layout.Iniciar_Ventana()
    
    #Cierra todas las funciones del mapa al salir en la ventana
    def on_pre_leave(self, *args):
        if hasattr(self.layout, 'Cerrar_Ventana'):
            self.layout.Cerrar_Ventana()
        if hasattr(self.layout, 'reiniciar_mapa'):
            self.layout.reiniciar_mapa()

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BAB_Screen(Screen):
    def __init__(self, **kwargs):
        super(BAB_Screen,self).__init__(**kwargs)
        self.layout= Layout_EventosFavoritos(self.abrir_otra_pantalla)
        self.add_widget(self.layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BAC_Screen(Screen):
    def __init__(self, **kwargs):
        super(BAC_Screen,self).__init__(**kwargs)
        self.layout= Layout_Cupones(self.abrir_otra_pantalla)
        self.add_widget(self.layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BAD_Screen(Screen):
    def __init__(self, **kwargs):
        super(BAD_Screen,self).__init__(**kwargs)
        self.layout= Layout_Suscripciones(self.abrir_otra_pantalla)
        self.add_widget(self.layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BB_Screen(Screen):
    def __init__(self, **kwargs):
        super(BB_Screen,self).__init__(**kwargs)
        layout= Layout_Organizador(self.abrir_otra_pantalla)
        self.add_widget(layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BBB_Screen(Screen):
    def __init__(self, **kwargs):
        super(BBB_Screen,self).__init__(**kwargs)
        layout= Layout_CreacionEventos(self.abrir_otra_pantalla)
        self.add_widget(layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


class BC_Screen(Screen):
    def __init__(self, **kwargs):
        super(BC_Screen,self).__init__(**kwargs)
        layout= Layout_Administrador(self.abrir_otra_pantalla)
        self.add_widget(layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla





class BuzzEvent(App):
    def build(self):
        self.ventana = BoxLayout(orientation='vertical',size_hint=(1,1))
        return self.ventana
    
    def on_start(self):
        self.Cargar_Builder()
        self.Cargar_Screens()
    
    def Cargar_Builder(self):
        Builder.load_file(r"Modulos_kivy/AA_Login.kv")
        Builder.load_file(r"Modulos_kivy/ABA_Recuperar_L.kv")
        Builder.load_file(r"Modulos_kivy/ACA_Registrar_L.kv")
        Builder.load_file(r"Modulos_kivy/BA_Estandar.kv")
        Builder.load_file(r"Modulos_kivy/BAA_Mapa.kv")
        Builder.load_file(r"Modulos_kivy/BAB_EventosFavoritos.kv")
        Builder.load_file(r"Modulos_kivy/BAC_Cupones.kv")
        Builder.load_file(r"Modulos_kivy/BAD_Suscripciones.kv")
        Builder.load_file(r"Modulos_kivy/BB_Organizador.kv")
        Builder.load_file(r"Modulos_kivy/BBB_CreacionEventos.kv")
        Builder.load_file(r"Modulos_kivy/BC_Administrador.kv")
    
    def Cargar_Screens(self):
        sm = ScreenManager()
        sm.add_widget(AA_Screen(name="AA_Login"))
        sm.add_widget(AB_Screen(name="ABA_Recuperar_L"))
        sm.add_widget(AC_Screen(name="ACA_Registrar_L"))
        sm.add_widget(BA_Screen(name="BA_Estandar"))
        sm.add_widget(BAA_Screen(name="BAA_Mapa"))
        sm.add_widget(BAB_Screen(name="BAB_EventosFavoritos"))
        sm.add_widget(BAC_Screen(name="BAC_Cupones"))
        sm.add_widget(BAD_Screen(name="BAD_Suscripciones"))
        sm.add_widget(BB_Screen(name="BB_Organizador"))
        sm.add_widget(BBB_Screen(name="BBB_CreacionEventos"))
        sm.add_widget(BC_Screen(name="BC_Administrador"))
        
        
        
        
        
        sm.current = "AA_Login"
        self.ventana.clear_widgets()
        self.ventana.add_widget(sm)