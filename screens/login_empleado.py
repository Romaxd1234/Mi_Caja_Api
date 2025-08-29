from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.resources import resource_add_path
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Rectangle, Color
from kivy.metrics import dp, sp
import requests
import os
from datetime import datetime, timedelta

API_URL = "https://mi-caja-api.onrender.com/tiendas"
HORAS_VIGENCIA = 8  # Tiempo de validez del login automático

class LoginEmpleadoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Ruta para guardar login automático (PC y Android)
        app_data_dir = App.get_running_app().user_data_dir if App.get_running_app() else r"C:\Invex"
        os.makedirs(app_data_dir, exist_ok=True)
        self.RUTA_TXT_EMPLEADO = os.path.join(app_data_dir, "empleado.txt")

        self.layout = FloatLayout()
        self.add_widget(self.layout)

        # Fondo con canvas
        ruta_assets = os.path.join(os.path.dirname(__file__), "assets")
        resource_add_path(ruta_assets)
        with self.layout.canvas.before:
            Color(1, 1, 1, 1)  # Fondo blanco si no carga la imagen
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.layout.pos, size=self.layout.size)
        self.layout.bind(size=self._update_rect, pos=self._update_rect)

        # Contenedor principal
        cont = BoxLayout(
            orientation='vertical', spacing=dp(15),
            size_hint=(0.85, 0.55), pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=[dp(20), dp(20), dp(20), dp(20)]
        )
        self.layout.add_widget(cont)

        # Título
        self.label_saludo = Label(
            text="👋 Hola, buen día",
            font_size=sp(28),
            size_hint=(1, 0.3),
            color=(0.1, 0.1, 0.1, 1),
            halign="center",
            valign="middle"
        )
        self.label_saludo.bind(size=self.label_saludo.setter('text_size'))
        cont.add_widget(self.label_saludo)

        # Spinner para empleados
        self.spinner_empleados = Spinner(
            text="Cargando empleados...",
            values=[],
            size_hint=(1, 0.25),
            background_color=(0.9, 0.9, 0.95, 1),
            color=(0,0,0,1),
            font_size=sp(16)
        )
        cont.add_widget(self.spinner_empleados)

        # Entrada de contraseña
        self.input_password = TextInput(
            hint_text="Contraseña",
            password=True,
            multiline=False,
            size_hint=(1, 0.25),
            font_size=sp(16),
            padding=[dp(10), dp(10)],
            background_color=(0.95, 0.95, 0.95, 1),
            foreground_color=(0,0,0,1)
        )
        cont.add_widget(self.input_password)

        # Botón iniciar sesión
        self.boton_login = Button(
            text="Iniciar sesión",
            size_hint=(1, 0.3),
            font_size=sp(16),
            background_color=(0.2, 0.6, 1, 1),
            color=(1,1,1,1)
        )
        cont.add_widget(self.boton_login)

        # Botón volver
        self.boton_volver = Button(
            text="Volver",
            size_hint=(0.25, 0.08),
            pos_hint={'x': 0.02, 'y': 0.02},
            background_color=(0.7, 0.7, 0.7, 1),
            color=(0,0,0,1),
            font_size=sp(14)
        )
        self.layout.add_widget(self.boton_volver)

        # Bindings
        self.boton_login.bind(on_release=self.intentar_login)
        self.boton_volver.bind(on_release=self.volver_a_seleccion_rol)

        # Variables
        self.tienda = None
        self.empleados = []

        # Intento de login automático al iniciar pantalla
        Clock.schedule_once(lambda dt: self.auto_login_empleado(), 0.1)

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.layout.pos
        self.fondo_rect.size = self.layout.size

    # --- Manejo de archivo empleado.txt ---
    def guardar_empleado_txt(self, nombre, password):
        with open(self.RUTA_TXT_EMPLEADO, "w") as f:
            f.write(f"{nombre},{password},{datetime.now().isoformat()}")

    def leer_empleado_txt(self):
        if os.path.exists(self.RUTA_TXT_EMPLEADO):
            try:
                with open(self.RUTA_TXT_EMPLEADO, "r") as f:
                    linea = f.read().strip()
                if linea:
                    nombre, password, ts = linea.split(",")
                    ts = datetime.fromisoformat(ts)
                    if datetime.now() - ts < timedelta(hours=HORAS_VIGENCIA):
                        return nombre, password
                    else:
                        self.eliminar_empleado_txt()
            except Exception:
                self.eliminar_empleado_txt()
        return None, None

    def eliminar_empleado_txt(self):
        if os.path.exists(self.RUTA_TXT_EMPLEADO):
            os.remove(self.RUTA_TXT_EMPLEADO)

    # --- Cargar empleados desde la API ---
    def set_datos_tienda_api(self, tienda):
        self.tienda = tienda
        self.cargar_empleados()

    def on_pre_enter(self):
        if self.tienda:
            self.cargar_empleados()

    def cargar_empleados(self):
        if not self.tienda or not self.tienda.get("id"):
            self.spinner_empleados.values = []
            self.spinner_empleados.text = "No hay empleados"
            return
        try:
            response = requests.get(f"{API_URL}/{self.tienda['id']}/empleados/")
            response.raise_for_status()
            self.empleados = response.json()
            nombres = [e.get("nombre", "") for e in self.empleados]
            if nombres:
                self.spinner_empleados.values = nombres
                self.spinner_empleados.text = nombres[0]
            else:
                self.spinner_empleados.values = []
                self.spinner_empleados.text = "No hay empleados"
        except Exception as e:
            self.spinner_empleados.values = []
            self.spinner_empleados.text = "Error al cargar empleados"
            print("Error al obtener empleados:", e)

    # --- Login ---
    def intentar_login(self, instance):
        nombre_sel = self.spinner_empleados.text
        contrasena = self.input_password.text.strip()

        if nombre_sel == "No hay empleados" or not nombre_sel:
            self.mostrar_popup("Error", "Por favor selecciona un empleado.")
            return

        emp = next((e for e in self.empleados if e.get("nombre") == nombre_sel), None)
        if not emp:
            self.mostrar_popup("Error", "Empleado no encontrado.")
            return

        if emp.get("password", "") == contrasena:
            self.guardar_empleado_txt(nombre_sel, contrasena)
            self.mostrar_popup("Éxito", f"Bienvenido {nombre_sel}")
            Clock.schedule_once(lambda dt: self.entrar_pantalla_principal(nombre_sel), 0.5)
        else:
            self.mostrar_popup("Error", "Contraseña incorrecta.")

    def auto_login_empleado(self):
        nombre, password = self.leer_empleado_txt()
        if nombre and password:
            emp = next((e for e in self.empleados if e.get("nombre") == nombre), None)
            if emp and emp.get("password") == password:
                Clock.schedule_once(lambda dt: self.entrar_pantalla_principal(nombre), 0.1)

    # --- Entrar a la pantalla principal ---
    def entrar_pantalla_principal(self, nombre_empleado):
        pantalla_principal = self.manager.get_screen("pantalla_principal")
        pantalla_principal.configurar_sesion(
            origen="empleado",
            nombre=nombre_empleado,
            tienda_id=self.tienda.get("id")
        )
        venta_inventario = self.manager.get_screen("venta_inventario")
        venta_inventario.nombre_usuario = nombre_empleado
        self.manager.current = "pantalla_principal"

    # --- Popups ---
    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        contenido.add_widget(Label(text=mensaje, font_size=sp(16), halign='center', valign='middle'))
        btn_cerrar = Button(text="Cerrar", size_hint=(1, None), height=dp(45), background_color=(0.2,0.6,1,1), color=(1,1,1,1))
        contenido.add_widget(btn_cerrar)
        popup = Popup(title=titulo, content=contenido, size_hint=(0.75, 0.35))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    # --- Volver ---
    def volver_a_seleccion_rol(self, instance):
        self.manager.current = "seleccion_rol"
