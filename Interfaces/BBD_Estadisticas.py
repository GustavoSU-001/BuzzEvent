from kivy.uix.boxlayout import BoxLayout
from Modulos.Singleton.Perfil import Singleton_Perfil
from kivy.uix.screenmanager import SlideTransition

import matplotlib.pyplot as plt
import numpy as np
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg




class Layout_Estadisticas(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Estadisticas,self).__init__(**kwargs)
        self.abrir_otra_pantalla= abrir_otra_pantalla
        #self.Cargar_Graficos()
        
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
    
    
    def Abrir_Ventana(self):
        rol=Singleton_Perfil.get_instance().tipo_perfil
        if rol != "Organizador":
            self.Abrir_Login()
        else:
            self.Cargar_Graficos()
        
    def Cerrar_Ventana(self):
        self.ids.Lista_Estadisticas.clear_widgets()
    
    
    def Cargar_Graficos(self):
        # Aquí se puede implementar la lógica para cargar y mostrar gráficos
        print("Cargando graficos de estadísticas...")
        datos = [
            {'tipo': 'Barras', 'titulo':'Gráfico de Barras: Ejemplo', 'titulo_y':'Valores', 'datos': [10, 20, 30, 40], 'etiquetas': ['A', 'B', 'C', 'D']},
            
            # === NUEVOS DATOS DE LÍNEA ===
            {'tipo': 'Linea', 'titulo':"Gráfico de Línea: Venta Mensual", 'datos': [50, 75, 60, 90, 80], 'etiquetas': ['Ene', 'Feb', 'Mar', 'Abr', 'May']},
            # ==============================
            
            {'tipo': 'Pastel', 'titulo':"Gráfico de Pastel: Distribución", 'datos': [25, 25, 25, 25], 'etiquetas': ['W', 'X', 'Y', 'Z']},
        ]
        
        # Limpiar gráficos previos antes de cargar nuevos
        self.ids.Lista_Estadisticas.clear_widgets() 
        
        for grafico in datos:
            # Propiedades de layout para asegurar que se muestren en el ScrollView
            layout_props = {'size_hint_y': None, 'height': '415dp'} 
            
            if grafico['tipo'] == 'Barras':
                barra = GraficoBarra(**layout_props)
                barra.crear_grafico(
                    titulo=grafico['titulo'],
                    titulo_y=grafico['titulo_y'],
                    etiquetas=grafico['etiquetas'],
                    valores=grafico['datos']
                )
                self.ids.Lista_Estadisticas.add_widget(barra)
            
            # === NUEVA LÓGICA PARA GRÁFICO DE LÍNEA ===
            elif grafico['tipo'] == 'Linea':
                linea = GraficoLinea(**layout_props)
                linea.crear_grafico(
                    titulo=grafico['titulo'],
                    etiquetas=grafico['etiquetas'],
                    valores=grafico['datos']
                )
                self.ids.Lista_Estadisticas.add_widget(linea)
            # ==========================================
            
            elif grafico['tipo'] == 'Pastel':
                pastel = GraficoPastel(**layout_props)
                pastel.crear_grafico(
                    titulo=grafico['titulo'],
                    etiquetas=grafico['etiquetas'],
                    valores=grafico['datos']
                )
                self.ids.Lista_Estadisticas.add_widget(pastel)
        
        
        
class GraficoBarra(BoxLayout):
    """
    Un widget de BoxLayout que contiene y genera un gráfico 
    de barras de Matplotlib.
    """
    def __init__(self, **kwargs):
        # Asegúrate de llamar al constructor del padre
        super().__init__(**kwargs)
        print("Creando gráfico de barras...")
        
        
        
        # Opcional: Establecer orientación, si la clase no se usa en un .kv
        # self.orientation = 'vertical' 
        
        # Llamamos al método para construir y añadir el gráfico

    def crear_grafico(self, titulo='Sin Titulo',titulo_y = 'Uso (%)',etiquetas=['A'], valores=[10]):
        # 1. Preparar los datos
        objects = etiquetas#('Python', 'C++', 'Java', 'Perl', 'Scala')
        y_pos = np.arange(len(objects))
        performance = valores#[10, 8, 6, 4, 2]

        w=4
        h=w/1.618
        
        # 2. Crear la figura y los ejes de Matplotlib
        fig, ax = plt.subplots(figsize=(w, h)) # Define el tamaño de la figura (opcional)

        # 3. Crear el gráfico de barras
        ax.bar(y_pos, performance, align='center', alpha=0.65, color='teal')
        
        # 4. Configurar etiquetas y título
        ax.set_xticks(y_pos) 
        ax.set_xticklabels(objects)
        ax.set_ylabel(titulo_y)    #   ('Uso (%)')
        ax.set_title(titulo) # ('Uso de Lenguajes')
        
        # 5. Integrar la figura de Matplotlib como un widget de Kivy
        chart_widget = FigureCanvasKivyAgg(fig)

        # 6. Añadir el widget del gráfico a esta instancia de BoxLayout
        self.add_widget(chart_widget)


class GraficoPastel(BoxLayout):
    """
    Un widget de BoxLayout que contiene y genera un gráfico 
    de pastel (Pie Chart) de Matplotlib, escalado correctamente.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chart_widget = None
        self.bind(size=self.update_chart)  # Enlazar el cambio de tamaño a la función update_chart

    def crear_grafico(self, titulo='Gráfico de Pastel', etiquetas=['A'], valores=[10]):
        # Guardamos los parámetros para poder redibujar el gráfico
        self.titulo = titulo
        self.etiquetas = etiquetas
        self.valores = valores
        
        # 1. Limpiar widgets anteriores (si los hay)
        if self.chart_widget:
            self.remove_widget(self.chart_widget)
            self.chart_widget = None

        # 2. Llamar a la función que realmente dibuja el gráfico
        # Esto se hará inmediatamente y cada vez que el tamaño cambie
        self.update_chart(self, self.size)


    def update_chart(self, instance, value):
        # Aseguramos que tenemos datos antes de dibujar y que el tamaño no es cero
        if not self.valores or self.size[0] == 0:
            return

        # Calcular el tamaño de la figura en pulgadas, manteniendo una relación de aspecto cuadrada.
        # Asumimos que quieres que el ancho y alto sean iguales al ancho del widget.
        # Convertimos píxeles de Kivy (self.width) a pulgadas (Matplotlib usa pulgadas).
        # DPI (Dots Per Inch) de Kivy por defecto es 96.
        dpi = 96
        width_inches = self.width / dpi
        
        # 1. Crear la figura y los ejes de Matplotlib. Usamos el ancho del widget para ambos.
        fig, ax = plt.subplots(figsize=(width_inches, width_inches)) 

        # 2. Reducir los márgenes internos de la figura para maximizar el área del pastel
        fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.01)

        # 3. Crear el gráfico de pastel
        ax.pie(self.valores, labels=self.etiquetas, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Garantiza que el pastel sea circular
        ax.set_title(self.titulo) 
        
        # 4. Integrar la figura de Matplotlib como un widget de Kivy
        chart_widget = FigureCanvasKivyAgg(fig)
        
        # 5. Si ya había un widget, lo reemplazamos
        if self.chart_widget:
            self.remove_widget(self.chart_widget)
            
        self.chart_widget = chart_widget
        self.add_widget(self.chart_widget)


# === NUEVA CLASE PARA GRÁFICO DE LÍNEA ===
class GraficoLinea(BoxLayout):
    """
    Un widget de BoxLayout que contiene y genera un gráfico 
    de línea de Matplotlib.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chart_widget = None
        self.bind(size=self.update_chart) 

    def crear_grafico(self, titulo='Gráfico de Línea', etiquetas=['Enero', 'Febrero', 'Marzo'], valores=[10, 15, 7]):
        # Guardamos los parámetros para poder redibujar el gráfico
        self.titulo = titulo
        self.etiquetas = etiquetas
        self.valores = valores
        
        if self.chart_widget:
            self.remove_widget(self.chart_widget)
            self.chart_widget = None

        self.update_chart(self, self.size)


    def update_chart(self, instance, value):
        if not self.valores or self.size[0] == 0:
            return

        # Calcular el tamaño de la figura en pulgadas, asumiendo una relación de aspecto de 5:4 (más ancha que alta)
        dpi = 96
        width_inches = self.width / dpi
        height_inches = width_inches * 0.8  # Un poco más bajo que ancho para el gráfico de línea
        
        # 1. Crear la figura y los ejes de Matplotlib.
        fig, ax = plt.subplots(figsize=(width_inches, height_inches)) 

        # 2. Reducir los márgenes internos de la figura
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15) 

        # 3. Crear el gráfico de línea
        x_pos = np.arange(len(self.etiquetas))
        
        # Añadir la línea principal
        ax.plot(x_pos, self.valores, marker='o', linestyle='-', color='blue', label='Datos')
        
        # Opcional: Añadir una cuadrícula para mejor lectura
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # 4. Configurar etiquetas y título
        ax.set_xticks(x_pos) 
        ax.set_xticklabels(self.etiquetas, rotation=45, ha='right') # Rota las etiquetas para que no se superpongan
        ax.set_ylabel("Valor") 
        ax.set_title(self.titulo)
        
        # 5. Integrar la figura de Matplotlib como un widget de Kivy
        chart_widget = FigureCanvasKivyAgg(fig)

        # 6. Añadir el widget del gráfico a esta instancia de BoxLayout
        if self.chart_widget:
            self.remove_widget(self.chart_widget)
            
        self.chart_widget = chart_widget
        self.add_widget(self.chart_widget)
















