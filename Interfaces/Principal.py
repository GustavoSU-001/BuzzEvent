from kivy.app import App
from kivy.uix.BoxLayout import BoxLayout




class BuzzEvent(App):
    def build(self):
        self.pantalla = BoxLayout(orientation='vertical')
        
        return self.pantalla