from Interfaces.Master import BuzzEvent
# Coloca esto al principio de main.py
import kivy
from kivy.config import Config
Config.set('kivy', 'copy_images', '0') # Evita que Kivy intente copiar sus íconos
Config.set('kivy', 'log_dir', 'logs') # Asegura un directorio de logs local.

kivy.require('2.3.1') # Asegura la versión de Kivy

BuzzEvent().run()



