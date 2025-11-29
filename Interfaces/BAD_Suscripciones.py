from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import SlideTransition
from kivy.properties import StringProperty, ColorProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label




class Layout_Suscripciones(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Suscripciones,self).__init__(**kwargs)
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
            
    def Abrir_Login(self):
        self.abrir_otra_pantalla("AA_Login", transition= SlideTransition(direction="right"))






############
class Singleton_Perfil:
    _instance = None
    def __init__(self):
        self.tipo_perfil = "Estandar" # O None, para probar el login

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    
# ---------------------------------------------------------


class Boton_Elemento(ButtonBehavior, BoxLayout, Label):
    """
    Corresponde a <Boton_Elemento@ButtonBehavior+BoxLayout+Label> en el KV.
    """
    # Definimos la propiedad para que Kivy sepa que existe y pueda asignarle color
    bg_color = ColorProperty((0.7, 1, 1, 1))

    def on_release(self):
        # Lógica cuando se presiona el botón "Comprar Suscripción"
        # Aquí podrías llamar a una pasarela de pago o imprimir en consola
        print("Botón presionado: Iniciando proceso de compra...")
        # Ejemplo: Acceder al padre para saber qué precio se está comprando
        if self.parent:
            # self.parent es Elemento_Suscripcion
            print(f"Comprando plan por valor de: {self.parent.valor}")

    def mostrar_mensaje_exito(self):
        # 1. Crear el contenido del mensaje
        layout_popup = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        mensaje = Label(
            text="¡La compra ha sido exitosa!\nGracias por suscribirte.",
            halign='center'
        )
        
        boton_cerrar = Button(
            text="Aceptar",
            size_hint=(1, None),
            height=40,
            background_color=(0, 0.8, 0, 1) # Botón verde
        )

        layout_popup.add_widget(mensaje)
        layout_popup.add_widget(boton_cerrar)

        # 2. Crear la ventana emergente (Popup)
        popup = Popup(
            title='Confirmación',
            content=layout_popup,
            size_hint=(0.7, 0.4), # Ocupa el 70% del ancho y 40% del alto
            auto_dismiss=False # Obliga a pulsar el botón para cerrar
        )

        # 3. Hacer que el botón cierre el popup
        boton_cerrar.bind(on_release=popup.dismiss)

        # 4. Mostrar el popup
        popup.open()
        
        # Opcional: Cambiar el texto del botón original para indicar que ya se compró
        self.text = "Suscripción Activa"
        self.bg_color = (0.5, 1, 0.5, 1) # Cambiar color a verde claro


class Elemento_Suscripcion(BoxLayout):
    """
    Representa cada tarjeta de suscripción ($20.000, etc.)
    """
    valor = StringProperty("$20.000")

# class Layout_Suscripciones(BoxLayout):
#     """
#     Pantalla principal de suscripciones.
#     """
#     def __init__(self, nav_callback=None, **kwargs):
#         # Capturamos el callback de navegación para evitar el error de __init__
#         self.callback_navegacion = kwargs.pop('nav_callback', None)
#         super().__init__(**kwargs)

#     def Regresar_MenuPrincipal(self, tipo_perfil):
#         # Lógica para volver a la pantalla anterior
#         print(f"Regresando al menú... Perfil: {tipo_perfil}")
        
#         if self.callback_navegacion:
#             self.callback_navegacion("nombre_pantalla_anterior")
#         else:
#             print("No hay función de navegación configurada.")
#             # Abrir_Login() # Fallback si fuera necesario

