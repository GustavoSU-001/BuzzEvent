class Singleton_Perfil:
    _instance = None

    @staticmethod
    def get_instance():
        if Singleton_Perfil._instance is None:
            Singleton_Perfil()
        return Singleton_Perfil._instance

    def __init__(self):
        if Singleton_Perfil._instance is not None:
            raise Exception("Esta clase es un Singleton. Usa get_instance() para obtener la instancia.")
        else:
            self.tipo_perfil = None
            Singleton_Perfil._instance = self