from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import requests
from datetime import datetime

class AbrirTiendaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout_principal = FloatLayout()

        # Fondo
        fondo = Image(source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                      allow_stretch=True, keep_ratio=False,
                      size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        layout_principal.add_widget(fondo)

        # Layout formulario
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15,
                           size_hint=(0.8, 0.7), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        layout.add_widget(Label(text="Abrir Tienda", font_size=24))
        layout.add_widget(Label(text="Nombre de la tienda"))
        self.nombre_input = TextInput(multiline=False)
        layout.add_widget(self.nombre_input)

        layout.add_widget(Label(text="Contraseña"))
        self.contra_input = TextInput(password=True, multiline=False)
        layout.add_widget(self.contra_input)

        self.msg = Label(text="", color=(1, 0, 0, 1))
        layout.add_widget(self.msg)

        btn_abrir = Button(text="Abrir Tienda", size_hint=(1, None), height=40)
        btn_abrir.bind(on_press=self.abrir_tienda)
        layout.add_widget(btn_abrir)

        btn_volver = Button(text="Volver", size_hint=(1, None), height=40)
        btn_volver.bind(on_press=self.volver)
        layout.add_widget(btn_volver)

        layout_principal.add_widget(layout)
        self.add_widget(layout_principal)

    def ventana(self, hora):
        return 1 if (hora >= 21 or hora < 7) else 0

    def necesita_login(self, ultimo_acceso):
        ahora = datetime.now()
        fecha_hoy = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.hour

        if not ultimo_acceso:
            return True

        fecha_acceso = ultimo_acceso.get("fecha")
        hora_acceso = int(ultimo_acceso.get("hora").split(":")[0])

        if fecha_acceso != fecha_hoy:
            return True

        return self.ventana(hora_acceso) != self.ventana(hora_actual)

    def verificar_ultimo_acceso(self, dt):
        nombre_tienda = self.nombre_input.text.strip()
        if not nombre_tienda:
            return

        try:
            url_api = f"https://mi-caja-api.onrender.com/tienda/{nombre_tienda}"
            response = requests.get(url_api)
            if response.status_code == 200:
                tienda_data = response.json()
                if not self.necesita_login(tienda_data.get("ultimo_acceso")):
                    self.manager.current = "seleccion_rol"
        except:
            pass  # Si falla la API, dejar que el usuario inicie sesión normalmente

    def abrir_tienda(self, instance):
        nombre = self.nombre_input.text.strip()
        contra = self.contra_input.text.strip()

        if not nombre or not contra:
            self.msg.text = "Por favor llena todos los campos"
            return

        try:
            url_login = "https://mi-caja-api.onrender.com/tienda/login"
            response = requests.post(url_login, json={"nombre": nombre, "patron_password": contra})

            if response.status_code == 200:
                # Guardar ultimo_acceso en la API
                ahora = datetime.now()
                acceso = {"fecha": ahora.strftime("%Y-%m-%d"), "hora": ahora.strftime("%H:%M")}
                url_actualizar = f"https://mi-caja-api.onrender.com/tienda/ultimo_acceso/{nombre}"
                requests.post(url_actualizar, json=acceso)

                self.msg.color = (0, 1, 0, 1)
                self.msg.text = "Tienda abierta correctamente"
                self.manager.current = "seleccion_rol"
            else:
                try:
                    error_msg = response.json().get("detail", "Nombre o contraseña incorrectos")
                except:
                    error_msg = "Nombre o contraseña incorrectos"
                self.msg.text = error_msg
        except Exception as e:
            self.msg.text = f"Error de conexión: {str(e)}"

    def volver(self, instance):
        self.manager.current = "bienvenida"
