from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.image import Image
import requests
from datetime import datetime

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class LoginEmpleadoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = FloatLayout()
        self.add_widget(self.layout)

        # Fondo
        fondo = Image(
            source=r'C:\Users\USER\Documents\APP\APP\assets\fondo.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout.add_widget(fondo)

        # Contenedor principal
        cont = BoxLayout(orientation='vertical', spacing=20,
                         size_hint=(0.8, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.layout.add_widget(cont)

        # Título
        self.label_saludo = Label(text="Hola buen día", font_size=32, size_hint=(1, 0.3), color=(0,0,0,1))
        cont.add_widget(self.label_saludo)

        # Spinner para empleados
        self.spinner_empleados = Spinner(
            text="Cargando empleados...",
            values=[],
            size_hint=(1, 0.3)
        )
        cont.add_widget(self.spinner_empleados)

        # Entrada de contraseña
        self.input_password = TextInput(
            hint_text="Contraseña",
            password=True,
            multiline=False,
            size_hint=(1, 0.3)
        )
        cont.add_widget(self.input_password)

        # Botón iniciar sesión
        self.boton_login = Button(text="Iniciar sesión", size_hint=(1, 0.3))
        cont.add_widget(self.boton_login)

        # Botón volver
        self.boton_volver = Button(
            text="Volver",
            size_hint=(0.15, 0.08),
            pos_hint={'x': 0.02, 'y': 0.02}
        )
        self.layout.add_widget(self.boton_volver)

        # Bindings
        self.boton_login.bind(on_release=self.intentar_login)
        self.boton_volver.bind(on_release=self.volver_a_seleccion_rol)

        # Variables
        self.tienda = None
        self.empleados = []

    def set_datos_tienda_api(self, tienda):
        """Recibe los datos de la tienda desde la API"""
        self.tienda = tienda
        self.cargar_empleados()
        print("Datos de la tienda cargados:", tienda)

    def on_pre_enter(self):
        """Se ejecuta antes de entrar a la pantalla"""
        if self.tienda:
            self.cargar_empleados()

    def cargar_empleados(self):
        """Carga los empleados desde la API y llena el spinner"""
        if not self.tienda or not self.tienda.get("id"):
            self.spinner_empleados.values = []
            self.spinner_empleados.text = "No hay empleados"
            return

        try:
            response = requests.get(f"{API_URL}/{self.tienda['id']}/empleados/")
            response.raise_for_status()
            empleados_lista = response.json()
            self.empleados = empleados_lista

            nombres = [emp.get("nombre", "") for emp in empleados_lista]
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

    def intentar_login(self, instance):
        """Valida la contraseña del empleado seleccionado"""
        nombre_seleccionado = self.spinner_empleados.text
        contrasena_ingresada = self.input_password.text.strip()

        if nombre_seleccionado == "No hay empleados" or not nombre_seleccionado:
            self.mostrar_popup("Error", "Por favor selecciona un empleado.")
            return

        empleado = next((e for e in self.empleados if e.get("nombre") == nombre_seleccionado), None)
        if empleado is None:
            self.mostrar_popup("Error", "Empleado no encontrado.")
            return

        if empleado.get("password", "") == contrasena_ingresada:
            self.mostrar_popup("Éxito", f"Bienvenido {nombre_seleccionado}")
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.entrar_pantalla_principal(nombre_seleccionado), 0.5)
        else:
            self.mostrar_popup("Error", "Contraseña incorrecta.")

    def entrar_pantalla_principal(self, nombre_empleado):
        pantalla_principal = self.manager.get_screen("pantalla_principal")
        pantalla_principal.configurar_sesion(
            origen="empleado",
            nombre=nombre_empleado,
            tienda_id=self.tienda.get("id")  # <-- así le pasas la tienda correcta
        )
        venta_inventario = self.manager.get_screen("venta_inventario")
        venta_inventario.nombre_usuario = nombre_empleado
        self.manager.current = "pantalla_principal"

    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=10, spacing=10)
        contenido.add_widget(Label(text=mensaje))
        btn_cerrar = Button(text="Cerrar", size_hint=(1, 0.3))
        contenido.add_widget(btn_cerrar)

        popup = Popup(title=titulo, content=contenido, size_hint=(0.6, 0.4))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def volver_a_seleccion_rol(self, instance):
        self.manager.current = "seleccion_rol"
