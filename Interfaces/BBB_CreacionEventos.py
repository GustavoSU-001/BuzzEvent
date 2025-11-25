
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.button import Button

from Modulos.Singleton.Perfil import Singleton_Perfil
from kivy.factory import Factory

import os
from openpyxl import load_workbook

try:
    from android.storage import primary_external_storage_path
    # Obtener la ruta del almacenamiento externo (típicamente /storage/emulated/0)
    DEFAULT_PATH = primary_external_storage_path() 
except ImportError:
    # Si no estamos en Android (estamos en Windows/Linux/macOS), usamos el directorio de usuario
    DEFAULT_PATH = os.path.expanduser('~')

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
        
    
    def Eliminar_TablaInvitados(self, widget, *args):
        """
        Elimina la tabla si la visibilidad es 'Publico'.
        El *args captura los argumentos extra del touch_up.
        """
        visibilidad = self.ids.visibilidad_spinner.text
        
        # 2. Aplicar la Condición: Solo eliminar si es 'Publico'
        if visibilidad == 'Publico': # Usamos "Publico" sin tilde, como lo tenías.
            print(f"Visibilidad '{visibilidad}': Eliminando widget.")
            
            # Eliminar el widget del contenedor
            self.ids.contenedor.clear_widgets([widget])
            
            # 💥 CRÍTICO: Limpiar la referencia para indicar que ya no existe 💥
            self.tabla_invitados_widget = None
            
            # ❌ LÍNEA ELIMINADA: Esto causaba el NameError (tabla no definida)
            # y trababa el spinner al intentar reasignar su on_touch_up.
            # self.ids.visibilidad_spinner.on_touch_up = lambda *args: self.Eliminar_TablaInvitados(tabla, *args)
            
        else:
            print(f"Visibilidad '{visibilidad}': No se permite la eliminación al tocar el widget.")
            return True # Indica que el evento fue manejado (detiene la propagación)
            
    def Agregar_TablaInvitados(self):
        visibilidad = self.ids.visibilidad_spinner.text
        
        # 1. Verificación de Visibilidad (Solo crear si es 'Privado')
        if visibilidad != 'Privado':
            print(f"Visibilidad '{visibilidad}': No se permite agregar tabla.")
            return
            
        # 2. 🛑 VERIFICACIÓN DE EXISTENCIA CON PROPIEDAD 🛑
        # Nota: Si no estás usando ObjectProperty, este código debería usar el for loop seguro.
        # Por ahora, mantengo el for loop hasta que confirmes la definición de ObjectProperty.
        for widget in self.ids.contenedor.children:
            if hasattr(widget, 'id') and widget.id == 'tabla_invitados':
                print("Advertencia: Ya existe una tabla de invitados. No se agregará otra.")
                return

        # Si la tabla ya existe, salimos
        # if self.tabla_invitados_widget:
        #     print("Advertencia: Ya existe una tabla de invitados. No se agregará otra.")
        #     return 
            
        # 3. Creación e inicialización
        tabla = Factory.Tabla_Invitados()
        tabla.id = 'tabla_invitados'
        
        # Guardar la referencia antes de añadir (Si usas ObjectProperty)
        # self.tabla_invitados_widget = tabla 
        
        # 4. Vinculación del Evento (en la tabla, no en el spinner)
        # Se vincula a la nueva instancia de 'tabla' para que se elimine al tocarla
        tabla.on_touch_up = lambda *args: self.Eliminar_TablaInvitados(tabla, *args)
        
        # ❌ LÍNEA ELIMINADA: Esto causaba la RecursionError y trababa el spinner.
        # self.ids.visibilidad_spinner.on_touch_down = self.Agregar_TablaInvitados()
        
        try:
            # 5. Añadir el widget
            self.ids.contenedor.add_widget(tabla)
            print("Tabla de invitados agregada exitosamente.")
        except Exception as e:
            print(f"Error al añadir tabla: {e}. Limpiando referencia.")
            # Si falla al añadir, limpiamos la referencia (Si usas ObjectProperty)
            # self.tabla_invitados_widget = None 
            pass
        

    
    def Formatear_NombreEvento(self):
        texto = self.ids.NombreEvento.text
        
        
        
        
        
        
        
    
    


