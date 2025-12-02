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
        # Cargar automáticamente la pestaña de Información al abrir
        self.Cargar_Informacion()
        
    def Cerrar_Ventana(self):
        # Limpiar la interfaz al salir
        self.ids.Interfaces_MisEventos.clear_widgets()
        Singleton_Evento.get_instance().id_evento = ''
        self.Imagenes = []
        self.id_evento = ''

    def Abrir_MisEventos(self):
        # Limpiar la interfaz antes de volver
        self.Cerrar_Ventana()
        
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
            self.Imagenes.insert(0, destination_path)
            print(f"Imagen copiada con código '{unique_code}' a: {destination_path}")
            
            # 4. Crear estructura de archivo para la base de datos
            archivo_data = {
                "Direccion": destination_path.replace('\\', '//'),
                "Extencion": ext.lower(),
                "Tipo": "Imagen",
                "Ubicacion": "img_interfaz"
            }
            
            # 5. Guardar en base de datos
            from Modulos.BaseDatos.Conexion import Escritura_Eventos_DB
            escritura = Escritura_Eventos_DB()
            escritura.agregar_archivo_evento(self.id_evento, archivo_data)
            
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
        
    def Cargar_Estadisticas(self):
        """
        Carga estadísticas del evento usando gráficos de matplotlib
        (usa las mismas clases que BBD_Estadisticas.py)
        """
        self.ids.Interfaces_MisEventos.clear_widgets()
        
        # Obtener datos del evento
        rut = Singleton_Perfil.get_instance().rut
        lect = Lectura_Eventos_DB()
        info = lect.obtener_informacion(rut)
        
        if self.id_evento not in info:
            print(f"❌ Evento {self.id_evento} no encontrado")
            return
        
        evento = info[self.id_evento]
        
        # Crear contenedor de estadísticas
        ag = Factory.Interfaz_Estadisticas()
        
        # 1. Gráfico de Líneas: Asistencia a lo largo del tiempo
        asistencia_dict = evento.get('Asistencia', {})
        if asistencia_dict:
            from datetime import datetime
            from collections import Counter
            
            # Extraer fechas de asistencia
            fechas_asistencia = []
            for id_asist, datos in asistencia_dict.items():
                if isinstance(datos, dict) and 'Fecha' in datos:
                    fecha_str = datos['Fecha']
                    try:
                        # Intentar parsear la fecha (puede venir en varios formatos)
                        if 'T' in fecha_str:
                            fecha = datetime.fromisoformat(fecha_str).date()
                        elif '-' in fecha_str and len(fecha_str.split('-')[0]) == 4:
                            # Formato YYYY-MM-DD
                            fecha = datetime.strptime(fecha_str.split()[0], '%Y-%m-%d').date()
                        else:
                            # Formato DD-MM-YYYY
                            fecha = datetime.strptime(fecha_str.split()[0], '%d-%m-%Y').date()
                        
                        fechas_asistencia.append(fecha)
                    except Exception as e:
                        print(f"Error al parsear fecha {fecha_str}: {e}")
                        continue
            
            # Contar asistencias por fecha
            if fechas_asistencia:
                contador_fechas = Counter(fechas_asistencia)
                fechas_ordenadas = sorted(contador_fechas.keys())
                
                # Preparar etiquetas y valores
                etiquetas_fechas = [f.strftime('%d/%m') for f in fechas_ordenadas]
                valores_asistencia = [contador_fechas[f] for f in fechas_ordenadas]
                
                grafico_linea = Factory.GraficoLinea(size_hint_y=None, height=415)
                grafico_linea.crear_grafico(
                    titulo='Asistencia al Evento por Fecha',
                    etiquetas=etiquetas_fechas,
                    valores=valores_asistencia
                )
                ag.ids.contenedor_graficos.add_widget(grafico_linea)
        
        # 2. Gráfico de Barras: Asistentes vs Participantes (con entrada)
        total_asistentes = len(asistencia_dict) if asistencia_dict else 0
        participantes_dict = evento.get('Participantes', {})
        total_participantes = len(participantes_dict) if participantes_dict else 0
        
        grafico_barras = Factory.GraficoBarra(size_hint_y=None, height=415)
        grafico_barras.crear_grafico(
            titulo='Asistentes vs Participantes',
            titulo_y='Personas',
            etiquetas=['Asistieron', 'Compraron Entrada'],
            valores=[total_asistentes, total_participantes]
        )
        ag.ids.contenedor_graficos.add_widget(grafico_barras)
        
        # 3. Gráfico de Pastel: Distribución de Calificaciones
        calificaciones = [a.get('Calificacion', 0) for a in evento.get('Asistencia', {}).values() if isinstance(a, dict)]
        if calificaciones:
            cal_5 = sum(1 for c in calificaciones if c >= 4.5)
            cal_4 = sum(1 for c in calificaciones if 3.5 <= c < 4.5)
            cal_3 = sum(1 for c in calificaciones if 2.5 <= c < 3.5)
            cal_bajo = sum(1 for c in calificaciones if c < 2.5)
            
            if any([cal_5, cal_4, cal_3, cal_bajo]):
                grafico_pastel = Factory.GraficoPastel(size_hint_y=None, height=415)
                grafico_pastel.crear_grafico(
                    titulo='Distribución de Calificaciones',
                    etiquetas=['★★★★★', '★★★★', '★★★', '< ★★★'],
                    valores=[cal_5, cal_4, cal_3, cal_bajo]
                )
                ag.ids.contenedor_graficos.add_widget(grafico_pastel)
        
        # 4. Gráfico de Mosaico: Categorías del Evento
        etiquetas = evento.get('Etiquetas', [])
        if etiquetas and len(etiquetas) > 0:
            valores = [100 // len(etiquetas)] * len(etiquetas)
            
            grafico_mosaico = Factory.GraficoMosaico(size_hint_y=None, height=415)
            grafico_mosaico.crear_grafico(
                titulo='Categorías del Evento',
                etiquetas=etiquetas,
                valores=valores
            )
            ag.ids.contenedor_graficos.add_widget(grafico_mosaico)
        
        self.ids.Interfaces_MisEventos.add_widget(ag)
            
            
    
    def Cargar_Informacion(self):
        self.ids.Interfaces_MisEventos.clear_widgets()
        rut = Singleton_Perfil.get_instance().rut
        lect = Lectura_Eventos_DB()
        lect = Lectura_Eventos_DB()
        info = lect.obtener_informacion(rut)
        print(f"DEBUG: Info cargada para {self.id_evento}: {info.get(self.id_evento, 'No encontrado')}")
        
        ag = Factory.Interfaz_Informacion()
        ag.ids.titulo_info.text = info[self.id_evento]['Titulo']
        ag.ids.descripcion_info.text = info[self.id_evento]['Descripcion']
        ag.ids.ubicacion_info.text = info[self.id_evento]['Ubicacion']
        ag.calificacion = info[self.id_evento]['Calificacion']
        
        # Agregar fechas con formato legible en campos editables
        fecha_inicio = info[self.id_evento].get('Fecha_Inicio', '')
        fecha_fin = info[self.id_evento].get('Fecha_Termino', '')
        
        # Formatear fechas para mostrar y editar (separar fecha y hora)
        try:
            from datetime import datetime
            if 'T' in fecha_inicio:
                dt_inicio = datetime.fromisoformat(fecha_inicio)
                ag.ids.fecha_inicio_edit.ids.usuario.text = dt_inicio.strftime('%d-%m-%Y')
                ag.ids.hora_inicio_edit.ids.usuario.text = dt_inicio.strftime('%H:%M')
            elif ' ' in fecha_inicio:
                partes = fecha_inicio.split(' ')
                ag.ids.fecha_inicio_edit.ids.usuario.text = partes[0]
                ag.ids.hora_inicio_edit.ids.usuario.text = partes[1] if len(partes) > 1 else '00:00'
            else:
                ag.ids.fecha_inicio_edit.ids.usuario.text = fecha_inicio
                ag.ids.hora_inicio_edit.ids.usuario.text = '00:00'
        except Exception as e:
            print(f"Error al cargar fecha inicio: {e}")
            ag.ids.fecha_inicio_edit.ids.usuario.text = ''
            ag.ids.hora_inicio_edit.ids.usuario.text = '00:00'
        
        try:
            if 'T' in fecha_fin:
                dt_fin = datetime.fromisoformat(fecha_fin)
                ag.ids.fecha_fin_edit.ids.usuario.text = dt_fin.strftime('%d-%m-%Y')
                ag.ids.hora_fin_edit.ids.usuario.text = dt_fin.strftime('%H:%M')
            elif ' ' in fecha_fin:
                partes = fecha_fin.split(' ')
                ag.ids.fecha_fin_edit.ids.usuario.text = partes[0]
                ag.ids.hora_fin_edit.ids.usuario.text = partes[1] if len(partes) > 1 else '00:00'
            else:
                ag.ids.fecha_fin_edit.ids.usuario.text = fecha_fin
                ag.ids.hora_fin_edit.ids.usuario.text = '00:00'
        except Exception as e:
            print(f"Error al cargar fecha fin: {e}")
            ag.ids.fecha_fin_edit.ids.usuario.text = ''
            ag.ids.hora_fin_edit.ids.usuario.text = '00:00'
        
        # Agregar precios
        try:
            precio_entrada = info[self.id_evento].get('Entrada', 0)
            ag.ids.precio_entrada_edit.text = str(precio_entrada) if precio_entrada else '0'
        except:
            ag.ids.precio_entrada_edit.text = '0'
        
        try:
            precio_preinscripcion = info[self.id_evento].get('Pre-inscripcion', 0)
            ag.ids.precio_preinscripcion_edit.text = str(precio_preinscripcion) if precio_preinscripcion else '0'
        except:
            ag.ids.precio_preinscripcion_edit.text = '0'
        
        # Agregar etiquetas interactivas
        todas_etiquetas = ['Música', 'Deportes', 'Arte', 'Tecnología', 'Comida', 
                          'Educación', 'Negocios', 'Entretenimiento', 'Salud', 
                          'Cine', 'Escolar', 'Formal', 'Informal', 'Familiar', 'Jovenes', 'Adultos']
        
        etiquetas_evento = info[self.id_evento].get('Etiquetas', [])
        
        for etiqueta in todas_etiquetas:
            etiq_widget = Factory.Etiquetas_Elementos()
            etiq_widget.text = etiqueta
            
            # Marcar como seleccionada si está en las etiquetas del evento
            if etiqueta in etiquetas_evento:
                etiq_widget.ids.seleccion.active = True
            
            # NO vincular evento de cambio automático - se guardará con el botón
            # etiq_widget.ids.seleccion.bind(...)
            
            ag.ids.lista_etiquetas.add_widget(etiq_widget)
        
        # Agregar referencia al layout para que los botones puedan acceder a los métodos
        ag.layout_ref = self
        
        self.ids.Interfaces_MisEventos.add_widget(ag)
    
    def Guardar_Cambios(self):
        """
        Guarda los cambios realizados en el evento.
        Valida que falte más de 1 semana para el inicio del evento.
        """
        from datetime import datetime, timedelta
        from Modulos.BaseDatos.Conexion import Escritura_Eventos_DB, Lectura_Eventos_DB
        
        try:
            # Obtener el widget de información
            if not self.ids.Interfaces_MisEventos.children:
                print("❌ No hay widget de información")
                return
            
            ag = self.ids.Interfaces_MisEventos.children[0]
            
            # Validar restricción de tiempo (1 semana antes del inicio)
            fecha_inicio_str = ag.ids.fecha_inicio_edit.ids.usuario.text
            hora_inicio_str = ag.ids.hora_inicio_edit.ids.usuario.text
            
            try:
                # Combinar fecha y hora
                fecha_hora_inicio = f"{fecha_inicio_str} {hora_inicio_str}"
                fecha_inicio = datetime.strptime(fecha_hora_inicio, '%d-%m-%Y %H:%M')
                
                # Calcular días restantes
                dias_restantes = (fecha_inicio - datetime.now()).days
                
                if dias_restantes < 7:
                    print(f"❌ No se puede editar: faltan menos de 7 días ({dias_restantes} días)")
                    print("   El evento debe iniciar en al menos 7 días para poder editarlo")
                    return
            except Exception as e:
                print(f"❌ Error al validar fecha: {e}")
                return
            
            # Recopilar cambios
            cambios = {}
            
            # Título
            cambios['Titulo'] = ag.ids.titulo_info.text
            
            # Descripción
            cambios['Descripcion'] = ag.ids.descripcion_info.text
            
            # Fechas (combinar fecha y hora, convertir a formato ISO)
            try:
                fecha_str = ag.ids.fecha_inicio_edit.ids.usuario.text
                hora_str = ag.ids.hora_inicio_edit.ids.usuario.text
                dt_inicio = datetime.strptime(f"{fecha_str} {hora_str}", '%d-%m-%Y %H:%M')
                cambios['Fechas.Fecha_Inicio'] = dt_inicio.isoformat()
            except Exception as e:
                print(f"Error al procesar fecha inicio: {e}")
                pass
            
            try:
                fecha_str = ag.ids.fecha_fin_edit.ids.usuario.text
                hora_str = ag.ids.hora_fin_edit.ids.usuario.text
                dt_fin = datetime.strptime(f"{fecha_str} {hora_str}", '%d-%m-%Y %H:%M')
                cambios['Fechas.Fecha_Termino'] = dt_fin.isoformat()
            except Exception as e:
                print(f"Error al procesar fecha fin: {e}")
                pass
            
            # Precios
            try:
                precio_entrada = int(ag.ids.precio_entrada_edit.text) if ag.ids.precio_entrada_edit.text else 0
                cambios['Acceso.Valor'] = precio_entrada
            except:
                pass
            
            try:
                precio_preinscripcion = int(ag.ids.precio_preinscripcion_edit.text) if ag.ids.precio_preinscripcion_edit.text else 0
                cambios['Visibilidad.Valor'] = precio_preinscripcion
            except:
                pass
            
            # Etiquetas (recopilar las seleccionadas)
            etiquetas_seleccionadas = []
            for etiq_widget in ag.ids.lista_etiquetas.children:
                if hasattr(etiq_widget.ids, 'seleccion') and etiq_widget.ids.seleccion.active:
                    if hasattr(etiq_widget, 'text'):
                        etiquetas_seleccionadas.append(etiq_widget.text)
            
            cambios['Etiquetas'] = etiquetas_seleccionadas
            
            # Actualizar en base de datos
            print(f"DEBUG: Enviando cambios a BD: {cambios}")
            escritura = Escritura_Eventos_DB()
            escritura.actualizar_evento_completo(self.id_evento, cambios)
            
            print(f"✅ Evento {self.id_evento} actualizado correctamente")
            
            # Recargar información para mostrar cambios guardados
            import time
            time.sleep(0.5) # Pequeña pausa para asegurar propagación
            self.Cargar_Informacion()
            
        except Exception as e:
            print(f"❌ Error al guardar cambios: {e}")
            import traceback
            traceback.print_exc()
    
    def actualizar_etiqueta_async(self, etiqueta, seleccionada):
        """
        Método vacío - las etiquetas ahora se guardan con el botón Guardar Cambios
        """
        pass
    
    def Cancelar_Evento(self):
        """Cancela el evento cambiando su estado a 'Cancelado'"""
        from Modulos.BaseDatos.Conexion import Escritura_Eventos_DB
        
        escritura = Escritura_Eventos_DB()
        escritura.cambiar_estado_evento(self.id_evento, 'Cancelado')
        
        print(f"Evento {self.id_evento} cancelado")
        
        # Recargar información para mostrar estado actualizado
        self.Cargar_Informacion()
        
        














