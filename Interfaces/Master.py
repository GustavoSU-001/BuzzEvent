from kivy.uix.actionbar import BoxLayout
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

from kivy.uix.screenmanager import NoTransition

from Interfaces.AA_Login import Layout_Login
from Interfaces.ABA_Recuperar_L import Layout_Recuperar_L
from Interfaces.ACA_Registrar_L import Layout_Registrar_L


class AA_Screen(Screen):
    def __init__(self, **kwargs):
        super(AA_Screen,self).__init__(**kwargs)
        layout= Layout_Login(self.abrir_otra_pantalla)
        self.add_widget(layout)

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla
       
        
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





class BuzzEvent(App):
    def build(self):
        self.ventana = BoxLayout(orientation='vertical',size_hint=(1,1))
        return self.ventana
    
    def on_start(self):
        self.Cargar_Builder()
        self.Cargar_Screens()
    
    def Cargar_Builder(self):
        Builder.load_file(r"Modelos_kivy/AA_Login.kv")
        Builder.load_file(r"Modelos_kivy/ABA_Recuperar_L.kv")
        Builder.load_file(r"Modelos_kivy/ACA_Registrar_L.kv")
    
    def Cargar_Screens(self):
        sm = ScreenManager()
        sm.add_widget(AA_Screen(name="AA_Login"))
        sm.add_widget(AB_Screen(name="ABA_Recuperar_L"))
        sm.add_widget(AC_Screen(name="ACA_Registrar_L"))
        
        
        
        
        
        sm.current = "AA_Login"
        self.ventana.clear_widgets()
        self.ventana.add_widget(sm)