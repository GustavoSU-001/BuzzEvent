from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import shutil
import os



class Layout_Estandar(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Estandar,self).__init__(**kwargs)
        self.abrir_otra_pantalla= abrir_otra_pantalla
        
    def Abrir_Mapa(self):
        self.abrir_otra_pantalla("BAA_Mapa", transition= SlideTransition(direction="left"))

    def cerrar_sesion(self):
        # Mostrar popup de confirmación
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Label(text='¿Desea cerrar sesión?', halign='center'))
        btns = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        btn_yes = Button(text='Sí')
        btn_no = Button(text='No')
        btns.add_widget(btn_yes)
        btns.add_widget(btn_no)
        content.add_widget(btns)

        popup = Popup(title='Confirmar', content=content, size_hint=(None, None), size=(400, 200))

        def _on_yes(instance):
            popup.dismiss()
            self._perform_logout_cleanup()

        def _on_no(instance):
            popup.dismiss()

        btn_yes.bind(on_release=_on_yes)
        btn_no.bind(on_release=_on_no)
        popup.open()

    def _perform_logout_cleanup(self):
        """Limpia cachés y tareas relacionadas antes de navegar al login."""
        try:
            # Eliminar carpetas de caché comunes
            dot_cache = os.path.join(os.getcwd(), '.cache')
            if os.path.exists(dot_cache):
                try:
                    shutil.rmtree(dot_cache)
                except Exception:
                    pass

            cache_dir = os.path.join(os.getcwd(), 'cache')
            if os.path.exists(cache_dir):
                try:
                    # opcional: solo borrar archivos dentro en lugar de toda la carpeta
                    shutil.rmtree(cache_dir)
                except Exception:
                    pass

            # Intentar detener y limpiar tareas de los layouts del mapa si existen
            try:
                app = App.get_running_app()
                sm = None
                # Buscar ScreenManager dentro de la ventana
                if hasattr(app, 'ventana') and app.ventana.children:
                    for child in app.ventana.children:
                        # importarlo aquí para no crear dependencia circular
                        from kivy.uix.screenmanager import ScreenManager
                        if isinstance(child, ScreenManager):
                            sm = child
                            break

                if sm:
                    # Lista de pantallas que pueden contener mapas o tareas activas
                    candidate_screens = ['BAA_Mapa']
                    for screen_name in candidate_screens:
                        try:
                            screen = sm.get_screen(screen_name)
                            if screen and screen.children:
                                layout = screen.children[0]
                                # intentar limpiar caché y desprogramar tareas
                                if hasattr(layout, 'buscar_y_limpiar_cache'):
                                    try:
                                        layout.buscar_y_limpiar_cache()
                                    except Exception:
                                        pass
                                if hasattr(layout, 'limpiar_cache'):
                                    try:
                                        Clock.unschedule(layout.limpiar_cache)
                                    except Exception:
                                        pass
                        except Exception:
                            pass
            except Exception:
                pass

        except Exception:
            pass

        # Finalmente, navegar a la pantalla de login
        try:
            self.abrir_otra_pantalla("AA_Login", transition= SlideTransition(direction="right"))
        except Exception:
            # Fallback simple: intentar obtener App y cambiar pantalla si es necesario
            try:
                app = App.get_running_app()
                if hasattr(app, 'ventana') and app.ventana.children:
                    for child in app.ventana.children:
                        from kivy.uix.screenmanager import ScreenManager
                        if isinstance(child, ScreenManager):
                            sm = child
                            sm.current = 'AA_Login'
                            break
            except Exception:
                pass