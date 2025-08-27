from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Rectangle
import requests
from kivy.resources import resource_add_path
import re
import os
from datetime import datetime, timedelta

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class AbrirTiendaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Definir ruta para guardar login automático (PC y Android)
        app_data_dir = App.get_running_app().user_data_dir
        os.makedirs(app_data_dir, exist_ok=True)
        self.TXT_PATH = os.path.join(app_data_dir, "tienda.txt")

        resource_add_path(os.path.join(os.path.dirname(__file__), "assets"))

        # Fondo con canvas
        with self.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)

        # Actualizar el tamaño del fondo al cambiar tamaño o posición
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Layout principal encima del fondo
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15,
                           size_hint=(0.8, 0.7),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})

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

        self.add_widget(layout)

        # Intentar abrir tienda automáticamente si hay login guardado
        Clock.schedule_once(lambda dt: self.auto_abrir_tienda(), 0)

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.pos
        self.fondo_rect.size = self.size

    def auto_abrir_tienda(self):
        if not os.path.exists(self.TXT_PATH):
            return
        try:
            with open(self.TXT_PATH, "r") as f:
                line = f.readline().strip()
                nombre, contra, ts = line.split(",")
                ts = datetime.fromisoformat(ts)
        except Exception:
            return  # Si falla leer, ignoramos

        # Si pasaron más de 8 horas, eliminar archivo
        if datetime.now() - ts > timedelta(hours=8):
            os.remove(self.TXT_PATH)
            return

        # Abrir tienda automáticamente
        self._abrir_tienda(nombre, contra)

    def abrir_tienda(self, instance):
        nombre = self.nombre_input.text.strip()
        contra = self.contra_input.text.strip()
        if not nombre or not contra:
            self.msg.text = "Por favor llena todos los campos"
            return

        self._abrir_tienda(nombre, contra)

    def _abrir_tienda(self, nombre, contra):
        tienda_id = self.obtener_id_por_nombre(nombre)
        if not tienda_id:
            self.msg.text = "La tienda no existe"
            return

        try:
            response = requests.get(f"{API_URL}/{tienda_id}")
            if response.status_code != 200:
                self.msg.text = "Error al conectar con la API"
                return

            tienda = response.json()
            if tienda.get("password", "").strip() == contra.strip():
                self.msg.text = "Tienda abierta correctamente"

                # Guardar login automático
                with open(self.TXT_PATH, "w") as f:
                    f.write(f"{nombre},{contra},{datetime.now().isoformat()}")

                # Pasar datos a otras pantallas
                if self.manager:
                    try:
                        pantalla_principal = self.manager.get_screen("pantalla_principal")
                        pantalla_principal.tienda_actual = tienda

                        pantalla_rol = self.manager.get_screen("seleccion_rol")
                        pantalla_rol.tienda_actual_id = tienda["id"]

                        inventario_screen = self.manager.get_screen("inventario")
                        inventario_screen.set_tienda_api(tienda)

                        self.manager.current = "seleccion_rol"
                    except Exception as e:
                        self.msg.text = f"Error interno: {str(e)}"
            else:
                self.msg.text = "Contraseña incorrecta"

        except Exception as e:
            self.msg.text = f"Error de conexión: {str(e)}"

    def obtener_id_por_nombre(self, nombre):
        try:
            response = requests.get(f"{API_URL}/")
            if response.status_code != 200:
                return None
            tiendas = response.json()
            nombre_limpio = re.sub(r'[\\/*?:"<>|]', "_", nombre.lower().replace(" ", "_"))
            tienda = next((t for t in tiendas if t["nombre"].lower().replace(" ", "_") == nombre_limpio), None)
            if tienda:
                return tienda["id"]
            return None
        except:
            return None

    def volver(self, instance):
        self.manager.current = "bienvenida"
