class Singleton_Evento:
    _instance = None

    @staticmethod
    def get_instance():
        if Singleton_Evento._instance is None:
            Singleton_Evento()
        return Singleton_Evento._instance

    def __init__(self):
        if Singleton_Evento._instance is not None:
            raise Exception("Esta clase es un Singleton. Usa get_instance() para obtener la instancia.")
        else:
            self.id_evento = None
            Singleton_Evento._instance = self