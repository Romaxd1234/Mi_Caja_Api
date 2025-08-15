from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
import requests

class SeleccionRolScreen(Screen):
    API_BASE = "https://mi-caja-api.onrender.com"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Fondo
        self.background = Image(
            source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
            allow_stretch=True, keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.add_widget(self.background)

        # Layout
        self.layout = BoxLayout(
            orientation='vertical',
            size_hint=(0.5, 0.5),
            spacing=20,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.nombre_label = Label(
            text="Cargando tienda...",
            font_size=32,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=50
        )

        self.btn_empleado = Button(text="Empleado", size_hint=(1, None), height=50)
        self.btn_patron = Button(text="Patrón", size_hint=(1, None), height=50)

        self.layout.add_widget(self.nombre_label)
        self.layout.add_widget(self.btn_empleado)
        self.layout.add_widget(self.btn_patron)
        self.add_widget(self.layout)

        # Estado
        self.tienda_actual = None

        # Handlers
        self.btn_empleado.bind(on_press=self.ir_pantalla_empleado)
        self.btn_patron.bind(on_press=self.ir_pantalla_patron)

    def on_pre_enter(self, *args):
        """
        Obtiene la tienda que se inició en la sesión desde la API
        y la muestra en la etiqueta.
        """
        try:
            r = requests.get(f"{self.API_BASE}/tienda", timeout=10)
            if r.status_code == 200:
                tiendas = r.json()
                # Aquí asumimos que la API devuelve una lista de tiendas
                # y que tu app guarda en la sesión cuál fue la abierta.
                # Vamos a buscar la primera activa (o puedes usar un endpoint /tienda/ultima)
                if tiendas:
                    # Por simplicidad, tomamos la primera tienda
                    self.tienda_actual = tiendas[0]["tienda"]["nombre"]
                    self.nombre_label.text = f"[b]Tienda: {self.tienda_actual}[/b]"
                    self.nombre_label.markup = True
                else:
                    self.nombre_label.text = "[b]No hay tiendas registradas[/b]"
                    self.nombre_label.markup = True
        except Exception as e:
            self.nombre_label.text = f"[b]Error al conectar API[/b]"
            self.nombre_label.markup = True

    def ir_pantalla_empleado(self, _):
        if not self.tienda_actual:
            self.nombre_label.text = "[b]No hay tienda seleccionada[/b]"
            self.nombre_label.markup = True
            return
        # Aquí navegarías a tu pantalla de login de empleado
        print(f"Navegando a login de empleado con tienda: {self.tienda_actual}")
        self.manager.current = "login_empleado"

    def ir_pantalla_patron(self, _):
        """
        Siempre pedimos login del patrón.
        Obtenemos la información del patrón desde la API
        y navegamos a PantallaPatronScreen.
        """
        if not self.tienda_actual:
            self.nombre_label.text = "[b]No hay tienda seleccionada[/b]"
            self.nombre_label.markup = True
            return

        try:
            # Obtener datos de la tienda desde la API
            url = f"{self.API_BASE}/tienda/{self.tienda_actual}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                patron_info = data.get("tienda", {})
                nombre_patron = patron_info.get("nombre", "Patrón")  # Nombre por default
            else:
                nombre_patron = "Patrón"
        except Exception:
            nombre_patron = "Patrón"

        # Navegar a PantallaPatronScreen
        pantalla_patron = self.manager.get_screen("pantalla_patron")
        pantalla_patron.set_datos_patron(nombre_patron, None)  # Aquí ya no usamos ruta local
        self.manager.current = "pantalla_patron"

    def set_tienda_actual(self, nombre_tienda):
        """
        Llamar desde AbrirTiendaScreen al hacer login exitoso
        """
        self.tienda_actual = nombre_tienda
        self.nombre_label.text = f"[b]Tienda: {self.tienda_actual}[/b]"
        self.nombre_label.markup = True
