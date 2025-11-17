
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button

from Modulos.Singleton.Perfil import Singleton_Perfil
from kivy.factory import Factory

import os
from openpyxl import load_workbook


class FileSelectPopup(Popup):
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
            path=os.path.expanduser('~') # Empieza en el directorio de usuario
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


class Tabla_Invitados(BoxLayout):
    identificador = []
    def __init__(self, **kwargs):
        super(Tabla_Invitados,self).__init__(**kwargs)
        
    def seleccionar_archivo(self, tipo):
        """Muestra el selector de archivos y define la función de manejo."""
        
        if tipo == 'xlsx':
            filters = ['*.xlsx']
            # Definir la función que manejará el archivo XLSX
            def on_file_selected(path):
                self.Importar_invitados(path)
        else:
            return

        popup = FileSelectPopup(
            select_callback=on_file_selected, 
            filters=filters
        )
        popup.open()
        
        
    def Agregar_invitado(self,rut="",fechas=None):
        invitado= Factory.Filas_ListaInvitados()
        invitado.accion= self.Agregar_fecha
        invitado.ids.rut_invitado.text= rut
        
        numero = 1
        
        while True:
            if numero not in self.identificador:
                invitado.id=numero
                self.identificador.append(numero)
                break
            else:
              numero +=1
              
        if fechas:
            print(fechas)
            for fecha in fechas:
                print(fecha)
                self.Agregar_fecha(invitado,fecha)
        
        self.ids.filas_invitados.add_widget(invitado)
        
    def Agregar_fecha(self,fila, listafechas=None):
        fecha= Factory.Fechas_ListaInvitados()
        print(listafechas)
        if listafechas:
            fecha.ids.fecha_inicio.text= listafechas[0] 
            fecha.ids.fecha_fin.text= listafechas[1]
           
        
        numero = 1
        while True:
            if numero not in self.identificador:
                fecha.id=numero
                self.identificador.append(numero)
                break
            else:
              numero +=1
        print(listafechas)
        fila.ids.fechas_invitado.add_widget(fecha)
        
    def Importar_invitados(self,ruta_archivo):
        try:
            # Reemplaza la simulación con la carga real de openpyxl
            wb = load_workbook(filename=ruta_archivo)
            sheet = wb.active
        except Exception as e:
            print(ruta_archivo)
            print(f"Error al cargar el archivo XLSX: {e}")
            return
        
        
        self.ids.filas_invitados.clear_widgets()
        datos_importados = [('11.111.111-2','2024-07-01 10:00','2024-07-01 12:00')]
        
        datos_formateados = {}
        for i, dato in enumerate(sheet.iter_rows(min_row=2, values_only=True)):    #datos_importados:
            datos_formateados.setdefault(str(dato[0]), []).append((str(dato[1]), str(dato[2])))
        #print(datos_formateados)
        for rut, fechas in datos_formateados.items():
            #print(fechas)
            self.Agregar_invitado(rut, fechas)
        



class Layout_CreacionEventos(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_CreacionEventos,self).__init__(**kwargs)
        self.abrir_otra_pantalla= abrir_otra_pantalla
        #self.Desplegar_Visibilidad()
        
    def Abrir_MenuPrincipal(self):
        rol = Singleton_Perfil.get_instance().tipo_perfil
        if rol == 'Estandar':
            self.abrir_otra_pantalla("BA_Estandar", transition=SlideTransition(direction="right"))
        elif rol == 'Organizador':
            self.abrir_otra_pantalla("BB_Organizador", transition=SlideTransition(direction="right"))
        elif rol == 'Administrador':
            self.abrir_otra_pantalla("BC_Administrador", transition=SlideTransition(direction="right"))
        else:
            self.abrir_otra_pantalla("AA_Login", transition=SlideTransition(direction="right"))
    
    
    def Abrir_Login(self):
        self.abrir_otra_pantalla("AA_Login", transition= SlideTransition(direction="right"))
        
        
        
        
        
        
    
    


