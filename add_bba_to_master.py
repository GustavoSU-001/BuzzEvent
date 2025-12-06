# Script to add BBA_Mapa registration to Master.py

with open('Interfaces/Master.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "from Interfaces.BAD_Suscripciones import Layout_Suscripciones"
# and add the BBA_Mapa import after it
for i, line in enumerate(lines):
    if 'from Interfaces.BAD_Suscripciones import Layout_Suscripciones' in line:
        lines.insert(i+2, '\n# Import BBA_Mapa\nfrom Interfaces.BBA_Mapa import Layout_Mapa as Layout_Mapa_BBA\n')
        break

# Find the line with 'Builder.load_file(r"Modulos_kivy/BAA_Mapa.kv")'
# and add BBA_Mapa.kv loading after it
for i, line in enumerate(lines):
    if 'Builder.load_file(r"Modulos_kivy/BAA_Mapa.kv")' in line:
        lines.insert(i+1, '        Builder.load_file(r"Modulos_kivy/BBA_Mapa.kv")\n')
        break

# Find the line with 'class BC_Screen(Screen):' and add BBA_Screen before it
for i, line in enumerate(lines):
    if 'class BC_Screen(Screen):' in line:
        bba_screen_code = '''
class BBA_Screen(Screen):
    def __init__(self, **kwargs):
        super(BBA_Screen,self).__init__(**kwargs)
        self.layout= Layout_Mapa_BBA(self.abrir_otra_pantalla)
        self.add_widget(self.layout)
        
    #Enciende todas las funciones del mapa al entrar en la ventana
    def on_pre_enter(self, *args):
        if hasattr(self.layout, 'Iniciar_Ventana'):
            self.layout.Iniciar_Ventana()
    
    #Cierra todas las funciones del mapa al salir en la ventana
    def on_pre_leave(self, *args):
        if hasattr(self.layout, 'Cerrar_Ventana'):
            self.layout.Cerrar_Ventana()

    def abrir_otra_pantalla(self, nueva_pantalla: str,transition= NoTransition):
        self.manager.transition = transition  # Set the transition for the screen change
        self.manager.current = nueva_pantalla


'''
        lines.insert(i, bba_screen_code)
        break

# Find the line with 'sm.add_widget(BC_Screen(name="BC_Administrador"))'
# and add BBA_Screen registration after it
for i, line in enumerate(lines):
    if 'sm.add_widget(BC_Screen(name="BC_Administrador"))' in line:
        lines.insert(i+1, '        sm.add_widget(BBA_Screen(name="BBA_Mapa"))\n')
        break

# Write the modified content back
with open('Interfaces/Master.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("BBA_Mapa successfully registered in Master.py")
