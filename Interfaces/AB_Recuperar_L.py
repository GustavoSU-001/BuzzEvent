from kivy.uix.boxlayout import BoxLayout




class Layout_Recuperar_L(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Recuperar_L,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        