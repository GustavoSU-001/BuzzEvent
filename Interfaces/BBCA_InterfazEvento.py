from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.button import Button

from Modulos.Singleton.Perfil import Singleton_Perfil
from Modulos.Singleton.Eventos import Singleton_Evento
from Modulos.BaseDatos.Conexion import Lectura_Eventos_DB

import matplotlib.pyplot as plt
import numpy as np
import os
from openpyxl import load_workbook
import shutil
import uuid

from kivy_garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.factory import Factory



try:
    from android.storage import primary_external_storage_path
    # Obtener la ruta del almacenamiento externo (típicamente /storage/emulated/0)
    DEFAULT_PATH = primary_external_storage_path() 
except ImportError:
    # Si no estamos en Android (estamos en Windows/Linux/macOS), usamos el directorio de usuario
    DEFAULT_PATH = os.path.expanduser('~')

class ImagenSelectPopup(Popup):
    def __init__(self, select_callback, filters, **kwargs):
        super().__init__(**kwargs)
        self.select_callback = select_callback
        self.title = 'Seleccionar Archivo de Invitados'
        self.size_hint = (0.9, 0.9)

        # Contenedor principal del popup
        content = BoxLayout(orientation='vertical', spacing=10)

        # 1. Selector de archivos
        self.filechooser = FileChooserListView(
            filters=filters,  # Filtros: ['*.xlsx', '*.json']
            multiselect=False,
            path=DEFAULT_PATH # Empieza en el directorio de usuario
        )
        content.add_widget(self.filechooser)

        # 2. Botones de acción
        action_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        btn_cancel = Button(text='Cancelar', size_hint_x=0.3)
        btn_cancel.bind(on_release=self.dismiss)
        action_layout.add_widget(btn_cancel)
        
        btn_select = Button(text='Seleccionar', size_hint_x=0.7)
        btn_select.bind(on_release=self.on_select)
        action_layout.add_widget(btn_select)

        content.add_widget(action_layout)
        self.content = content

    def on_select(self, instance):
        if self.filechooser.selection:
            # Obtener la ruta del archivo seleccionado
            selected_file = self.filechooser.selection[0]
            self.select_callback(selected_file)
            self.dismiss()
        else:
            print("No se ha seleccionado ningún archivo.")



class Layout_InterfazEvento(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_InterfazEvento,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        self.Imagenes = []
        self.id_evento=''

    def Abrir_Ventana(self):
        self.id_evento = Singleton_Evento.get_instance().id_evento
        self.descargar_imagenes()
        
    def Cerrar_Ventana(self):
        Singleton_Evento.get_instance().id_evento = ''
        self.Imagenes=[]

    def Abrir_MisEventos(self):
        rol = Singleton_Perfil.get_instance().tipo_perfil
        if rol == 'Organizador':
            self.abrir_otra_pantalla("BBC_MisEventos", transition=SlideTransition(direction="right"))
        else:
            self.abrir_otra_pantalla("AA_Login", transition=SlideTransition(direction="right"))
            
    def Abrir_Login(self):
        self.abrir_otra_pantalla("AA_Login", transition= SlideTransition(direction="right"))
        
        
    def seleccionar_archivo(self):
        """Muestra el selector de archivos y define la función de manejo."""
        
        #if tipo in ['xlsx']:
        filters = ['*.jpg','*.jpeg','*.png']
        # Definir la función que manejará el archivo XLSX
        def on_file_selected(path):
            self.subir_imagen(path)
        #else:
        #    return

        popup = ImagenSelectPopup(
            select_callback=on_file_selected, 
            filters=filters
        )
        popup.open()
        
    def subir_imagen(self,source_path):
        """
        Simplificado: Copia la imagen a un directorio local con un nombre único
        y guarda la ruta interna en event_images.
        """
        if not source_path or not os.path.exists(source_path):
            print("Error: Ruta de imagen no válida.")
            return

        try:
            # 1. Definir la carpeta de destino segura dentro de los datos de la app
            target_dir = 'Static\\Eventos\\Imagenes'
            os.makedirs(target_dir, exist_ok=True)
            
            # 2. Crear código único y ruta de destino
            unique_code = uuid.uuid4().hex
            _, ext = os.path.splitext(source_path)
            new_filename = f"{unique_code}{ext.lower()}"
            destination_path = os.path.join(target_dir, new_filename)

            # 3. Copiar la imagen y guardar la referencia
            shutil.copyfile(source_path, destination_path)
            self.Imagenes.insert(0,destination_path)
            print(f"Imagen copiada con código '{unique_code}' a: {destination_path}")
            self.Cargar_Imagenes()

        except Exception as e:
            print(f"Error al subir o copiar la imagen: {e}")
        
    def descargar_imagenes(self):
        rut = Singleton_Perfil.get_instance().rut
        lect = Lectura_Eventos_DB()
        info = lect.obtener_informacion(rut)
        print(self.id_evento)
        self.Imagenes = info[self.id_evento]['Imagenes']
        
    
        
        
    def Cargar_Imagenes(self):
        self.ids.Interfaces_MisEventos.clear_widgets()
        
        
        for i, imag in enumerate(self.Imagenes):
            imagen = Factory.Interfaz_Imagenes()
            imagen.id=i
            imagen.imagen=imag
            self.ids.Interfaces_MisEventos.add_widget(imagen)
        if len(self.Imagenes) < 1:
            imagen = Factory.Interfaz_Imagenes()
            imagen.imagen='Static\Imagenes\obras.png'
            self.ids.Interfaces_MisEventos.add_widget(imagen)
        ag=Factory.Agregar()
        ag.on_release=self.seleccionar_archivo
        self.ids.Interfaces_MisEventos.add_widget(ag)
        
            
    
    def Cargar_Informacion(self):
        self.ids.Interfaces_MisEventos.clear_widgets()
        rut=Singleton_Perfil.get_instance().rut
        lect = Lectura_Eventos_DB()
        info = lect.obtener_informacion(rut)
        
        
        ag=Factory.Interfaz_Informacion()
        ag.ids.titulo_info.text=info[self.id_evento]['Titulo']
        ag.ids.descripcion_info.text=info[self.id_evento]['Descripcion']
        ag.ids.ubicacion_info.text=info[self.id_evento]['Ubicacion']['Direccion']
        ag.calificacion = info[self.id_evento]['Calificacion']
        self.ids.Interfaces_MisEventos.add_widget(ag)
        
        














