from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.app import App
import uuid
#from jnius import autoclass
from kivy.graphics import Rectangle
import requests
from kivy.resources import resource_add_path
import re
import os
from datetime import datetime, timedelta

import sys
if sys.platform == "win32":
    class Dummy:
        def __getattr__(self, name):
            return lambda *a, **k: None
    autoclass = lambda name: Dummy()
    print("✅ abrir_tienda.py cargado, usando mock de PyJNIus en Windows")
else:
    from jnius import autoclass

API_URL = "https://mi-caja-api.onrender.com/tiendas"

def get_device_uuid():
    try:
        # Android nativo
        Secure = autoclass('android.provider.Settings$Secure')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        context = PythonActivity.mActivity.getContentResolver()
        android_id = Secure.getString(context, Secure.ANDROID_ID)
        return android_id
    except:
        # Fallback: UUID persistente en disco
        app_data_dir = App.get_running_app().user_data_dir
        uuid_path = os.path.join(app_data_dir, "device_uuid.txt")
        if os.path.exists(uuid_path):
            with open(uuid_path, "r") as f:
                return f.read().strip()
        new_uuid = str(uuid.uuid4())
        with open(uuid_path, "w") as f:
            f.write(new_uuid)
        return new_uuid

class AbrirTiendaScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Directorio de datos de la app
        app_data_dir = App.get_running_app().user_data_dir
        os.makedirs(app_data_dir, exist_ok=True)
        self.TXT_PATH = os.path.join(app_data_dir, "tienda.txt")

        # Fondo con canvas
        with self.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # Layout principal
        layout = BoxLayout(
            orientation='vertical',
            padding=[20, 20, 20, 20],
            spacing=15,
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        layout.add_widget(Label(text="Abrir Tienda", font_size='24sp', size_hint=(1, None), height='40dp'))
        layout.add_widget(Label(text="Nombre de la tienda", size_hint=(1, None), height='30dp'))
        self.nombre_input = TextInput(multiline=False, size_hint=(1, None), height='40dp')
        layout.add_widget(self.nombre_input)
        layout.add_widget(Label(text="Contraseña", size_hint=(1, None), height='30dp'))
        self.contra_input = TextInput(password=True, multiline=False, size_hint=(1, None), height='40dp')
        layout.add_widget(self.contra_input)
        self.msg = Label(text="", color=(1, 0, 0, 1), size_hint=(1, None), height='30dp')
        layout.add_widget(self.msg)

        btn_abrir = Button(text="Abrir Tienda", size_hint=(1, None), height='45dp')
        btn_abrir.bind(on_press=self.abrir_tienda)
        layout.add_widget(btn_abrir)

        btn_volver = Button(text="Volver", size_hint=(1, None), height='45dp')
        btn_volver.bind(on_press=self.volver)
        layout.add_widget(btn_volver)

        self.add_widget(layout)
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
            return
        if datetime.now() - ts > timedelta(hours=8):
            os.remove(self.TXT_PATH)
            return
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
            if tienda.get("password", "").strip() != contra.strip():
                self.msg.text = "Contraseña incorrecta"
                return

            # 🔹 CONTROL DE DISPOSITIVOS
            uuid_dispositivo = get_device_uuid()
            devices_resp = requests.get(f"{API_URL}/{tienda_id}/dispositivos/")
            devices = []
            if devices_resp.status_code == 200:
                devices = devices_resp.json().get("dispositivos_registrados", [])

            max_allowed = tienda.get("dispositivos_permitidos", 2)

            if uuid_dispositivo in devices:
                pass  # ya registrado
            elif len(devices) >= max_allowed:
                self.msg.text = "Se alcanzó el límite de dispositivos permitidos"
                return
            else:
                reg_resp = requests.post(f"{API_URL}/{tienda_id}/dispositivos/", json={"uuid": uuid_dispositivo})
                if reg_resp.status_code not in (200, 201):
                    self.msg.text = "No se pudo registrar el dispositivo (límite alcanzado)"
                    return
                print(f"✅ Dispositivo registrado: {uuid_dispositivo}")

            # Guardar TXT con timestamp
            with open(self.TXT_PATH, "w") as f:
                f.write(f"{nombre},{contra},{datetime.now().isoformat()}")

            self.msg.text = "Tienda abierta correctamente"

            # Pasar la tienda a otras pantallas
            if self.manager:
                try:
                    ventas_screen = self.manager.get_screen("pantalla_principal")
                    ventas_screen.configurar_sesion(
                        empleado=None,
                        tienda=tienda,
                        tienda_id=tienda["id"],
                        nombre=None,
                        origen="patron"
                    )
                    ventas_screen.cargar_tienda_api()

                    pantalla_rol = self.manager.get_screen("seleccion_rol")
                    pantalla_rol.tienda_actual_id = tienda["id"]

                    inventario_screen = self.manager.get_screen("inventario")
                    inventario_screen.set_tienda_api(tienda)

                    self.manager.current = "seleccion_rol"
                except Exception as e:
                    self.msg.text = f"Error interno: {str(e)}"

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