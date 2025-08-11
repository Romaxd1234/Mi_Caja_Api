from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.storage.jsonstore import JsonStore
from functools import partial
import os
from datetime import datetime

class LoginEmpleadoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = FloatLayout()
        self.add_widget(self.layout)

        # Fondo igual que en otras ventanas
        fondo = Image(
            source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout.add_widget(fondo)

        # Contenedor principal vertical
        cont = BoxLayout(orientation='vertical', spacing=20,
                         size_hint=(0.8, 0.5), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.layout.add_widget(cont)

        # Título
        self.label_saludo = Label(text="Hola buen día", font_size=32, size_hint=(1, 0.3), color=(0,0,0,1))
        cont.add_widget(self.label_saludo)

        # Spinner para empleados (vacío por ahora)
        self.spinner_empleados = Spinner(
            text="Selecciona tu nombre",
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

        # Botón volver en esquina inferior izquierda
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
        self.ruta_tienda = None
        self.empleados = []

    def ventana(self, hora):
        # 1 = noche (21:00 a 6:59), 0 = día (7:00 a 20:59)
        return 1 if (hora >= 21 or hora < 7) else 0

    def necesita_login(self):
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            return True

        store = JsonStore(self.ruta_tienda)
        if not store.exists("ultimo_acceso_empleado"):
            return True

        acceso = store.get("ultimo_acceso_empleado")
        fecha_acceso = acceso.get("fecha")
        hora_acceso = int(acceso.get("hora").split(":")[0])

        ahora = datetime.now()
        fecha_hoy = ahora.strftime("%Y-%m-%d")
        hora_actual = ahora.hour

        if fecha_acceso != fecha_hoy:
            return True

        ventana_acceso = self.ventana(hora_acceso)
        ventana_actual = self.ventana(hora_actual)

        return ventana_acceso != ventana_actual

    def obtener_ultimo_empleado_logueado(self):
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            return None
        store = JsonStore(self.ruta_tienda)
        if store.exists("ultimo_empleado"):
            return store.get("ultimo_empleado")["nombre"]
        return None

    def on_pre_enter(self):
        # Se ejecuta antes de entrar a la pantalla para cargar empleados
        self.cargar_empleados()

        if not self.necesita_login():
            ultimo_empleado = self.obtener_ultimo_empleado_logueado()
            if ultimo_empleado:
                self.entrar_pantalla_principal(ultimo_empleado)

    def set_ruta_tienda(self, ruta):
        self.ruta_tienda = ruta

    def cargar_empleados(self):
        self.empleados = []
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            self.spinner_empleados.values = []
            self.spinner_empleados.text = "No hay empleados"
            return

        store = JsonStore(self.ruta_tienda)
        if store.exists("empleados"):
            empleados_lista = store.get("empleados").get("lista", [])
            self.empleados = empleados_lista
            nombres = [emp.get("nombre", "") for emp in empleados_lista]
            if nombres:
                self.spinner_empleados.values = nombres
                self.spinner_empleados.text = nombres[0]
            else:
                self.spinner_empleados.values = []
                self.spinner_empleados.text = "No hay empleados"
        else:
            self.spinner_empleados.values = []
            self.spinner_empleados.text = "No hay empleados"

    def intentar_login(self, instance):
        nombre_seleccionado = self.spinner_empleados.text
        contrasena_ingresada = self.input_password.text.strip()

        if nombre_seleccionado == "No hay empleados" or not nombre_seleccionado:
            self.mostrar_popup("Error", "Por favor selecciona un empleado.")
            return

        # Buscar empleado y validar contraseña
        empleado = next((e for e in self.empleados if e.get("nombre") == nombre_seleccionado), None)

        if empleado is None:
            self.mostrar_popup("Error", "Empleado no encontrado.")
            return

        if empleado.get("password", "") == contrasena_ingresada:
            # Guardar último login empleado con fecha y hora
            ahora = datetime.now()
            store = JsonStore(self.ruta_tienda)
            store.put("ultimo_acceso_empleado", fecha=ahora.strftime("%Y-%m-%d"), hora=ahora.strftime("%H:%M"))
            store.put("ultimo_empleado", nombre=nombre_seleccionado)

            self.mostrar_popup("Éxito", f"Bienvenido {nombre_seleccionado}")
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self.entrar_pantalla_principal(nombre_seleccionado), 0.5)
        else:
            self.mostrar_popup("Error", "Contraseña incorrecta.")

    def entrar_pantalla_principal(self, nombre_empleado):
        pantalla_principal = self.manager.get_screen("pantalla_principal")
        pantalla_principal.configurar_sesion(origen="empleado", nombre=nombre_empleado)

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

    def guardar_sesion_local_empleado(self, nombre_empleado):
        sesion = {
            "nombre": nombre_empleado,
            "rol": "empleado"
        }
        with open("session_local.json", "w", encoding="utf-8") as f:
            json.dump(sesion, f, indent=4)
