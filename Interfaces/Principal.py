from kivy.app import App
from kivy.uix.boxlayout import BoxLayout




class BuzzEvent(App):
    def build(self):
        self.pantalla = BoxLayout(orientation='vertical')
        
        return self.pantalla