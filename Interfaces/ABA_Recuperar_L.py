from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition
from kivy.clock import Clock



class Layout_Recuperar_L(BoxLayout):
    def __init__(self, abrir_otra_pantalla, **kwargs):
        super(Layout_Recuperar_L,self).__init__(**kwargs)
        self.abrir_otra_pantalla = abrir_otra_pantalla
        self.Ingresar_Correo_o_Telefono()
        
    def Ingresar_Correo_o_Telefono(self,dt=None):
        self.ids.img_recuperar.size_hint_y=0
        self.ids.img_recuperar.opacity=0
        self.ids.lbl_recuperar.size_hint_y=1
        self.ids.lbl_recuperar.text = "Ingrese su Correo Electrónico o Teléfono asociados a tu cuenta para recuperar tu contraseña."
        self.ids.inp_recuperar_p.t_text = 'Correo Electrónico o Teléfono'
        self.ids.inp_recuperar_p.opacity = 1
        self.ids.inp_recuperar_p.disabled = False
        self.ids.box_btn_recuperar.size_hint_y=0.5
        self.ids.btn_recuperar.accion=self.Verificar_Codigo
        self.ids.btn_recuperar.text = 'Siguiente'
        
    def Verificar_Codigo(self):
        self.ids.lbl_recuperar.text = "Se le ha enviado un código a su correo guixxxxxx@gmail.com para su verificación."
        self.ids.inp_recuperar_p.t_text = 'Código de Verificación'
        self.ids.btn_recuperar.accion=self.Guardar_Contraseña
    
    def Guardar_Contraseña(self):
        self.ids.lbl_recuperar.text = "Ingrese su nueva contraseña, esta no debe de ser igual a sus ultimas tres contraseñas anteriores."
        self.ids.inp_recuperar_p.t_text = 'Nueva Contraseña'
        self.ids.inp_recuperar_s.t_text = 'Confirmar Nueva Contraseña'
        self.ids.inp_recuperar_s.opacity = 1
        self.ids.inp_recuperar_s.disabled = False
        self.ids.btn_recuperar.accion=self.Resultado_Recuperar
        self.ids.btn_recuperar.text = 'Cambiar Contraseña'
        
    def Resultado_Recuperar(self):
        self.ids.img_recuperar.size_hint_y=0.5
        self.ids.img_recuperar.opacity=1
        self.ids.lbl_recuperar.size_hint_y=0.2
        self.ids.lbl_recuperar.text = "Su contraseña ha sido cambiada exitosamente."
        self.ids.inp_recuperar_p.opacity = 0
        self.ids.inp_recuperar_p.disabled = True
        self.ids.inp_recuperar_s.opacity = 0
        self.ids.inp_recuperar_s.disabled = True
        self.ids.box_btn_recuperar.size_hint_y=0.2
        self.ids.btn_recuperar.accion=self.Volver_Login
        self.ids.btn_recuperar.text = 'Volver al Login'
        
    def Volver_Login(self):
        self.abrir_otra_pantalla('AA_Login',transition= SlideTransition(direction="right"))
        Clock.schedule_once(lambda dt: self.Ingresar_Correo_o_Telefono(), 1)
        
        
        