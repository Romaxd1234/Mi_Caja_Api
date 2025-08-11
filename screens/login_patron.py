from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
import os
from datetime import datetime

class LoginPatronScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Fondo
        self.background = Image(source='C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                                allow_stretch=True,
                                keep_ratio=False,
                                size_hint=(1, 1),
                                pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.add_widget(self.background)

        # Layout principal
        self.layout = BoxLayout(orientation='vertical',
                                spacing=20,
                                size_hint=(0.5, 0.5),
                                pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # Label saludo, inicialmente genérico
        self.label = Label(text="Hola, patrón", font_size=24, color=(1, 1, 1, 1))
        # Campo para contraseña, oculto
        self.input_contrasena = TextInput(hint_text="Contraseña", multiline=False, password=True, size_hint=(1, None), height=40)

        self.boton_ingresar = Button(text="Ingresar", size_hint=(1, None), height=40)
        self.boton_regresar = Button(text="Regresar", size_hint=(1, None), height=40)

        self.boton_ingresar.bind(on_release=self.verificar_patron)
        self.boton_regresar.bind(on_release=self.regresar)

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.input_contrasena)
        self.layout.add_widget(self.boton_ingresar)
        self.layout.add_widget(self.boton_regresar)

        self.add_widget(self.layout)

        # Variables para datos patrón
        self.nombre_patron = ""
        self.ruta_tienda = None

    def set_datos_patron(self, ruta_tienda):
        self.ruta_tienda = ruta_tienda
        if os.path.exists(ruta_tienda):
            store = JsonStore(ruta_tienda)
            if store.exists("patron"):
                self.nombre_patron = store.get("patron")["nombre"]
                self.label.text = f"Hola, {self.nombre_patron}"

    def verificar_patron(self, instance):
        contrasena_ingresada = self.input_contrasena.text.strip()

        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            self.mostrar_popup("Error", "No se encontró el archivo de la tienda.")
            return

        store = JsonStore(self.ruta_tienda)
        if store.exists("patron"):
            contrasena_guardada = store.get("patron")["password"]
            if contrasena_ingresada == contrasena_guardada:
                if self.esta_en_horario_login() and not self.ya_hizo_login_hoy(store):
                    ahora = datetime.now()
                    store.put("log_nocturno", fecha=ahora.strftime("%Y-%m-%d"), hora=ahora.strftime("%H:%M"))
                    print("Se guardó el login nocturno en el JSON")  # Para depurar
                self.mostrar_popup("Éxito", f"Bienvenido, {self.nombre_patron}.")

                # Llamar configurar_sesion y cambiar a pantalla principal
                pantalla_principal = self.manager.get_screen("pantalla_principal")
                pantalla_principal.configurar_sesion(origen="patron", nombre=self.nombre_patron)
                self.manager.current = "pantalla_principal"

                self.input_contrasena.text = ""  # Limpiar campo contraseña

            else:
                self.mostrar_popup("Error", "Contraseña incorrecta.")
        else:
            self.mostrar_popup("Error", "No hay patrón registrado en esta tienda.")

    def regresar(self, instance):
        self.manager.current = "seleccion_rol"

    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', spacing=10)
        contenido.add_widget(Label(text=mensaje))
        cerrar = Button(text="Cerrar", size_hint=(1, 0.3))
        popup = Popup(title=titulo, content=contenido, size_hint=(0.6, 0.4))
        cerrar.bind(on_release=popup.dismiss)
        contenido.add_widget(cerrar)
        popup.open()

    def esta_en_horario_login(self):
        ahora = datetime.now()
        hora = ahora.hour
        return hora >= 21 or hora < 7  # Entre 21:00 y 06:59

    def ya_hizo_login_hoy(self, store):
        if store.exists("log_nocturno"):
            fecha_guardada = store.get("log_nocturno")["fecha"]
            hoy = datetime.now().strftime("%Y-%m-%d")
            return fecha_guardada == hoy
        return False
