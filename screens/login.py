from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.storage.jsonstore import JsonStore

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', spacing=15, padding=40)

        layout.add_widget(Label(text="Iniciar sesión", font_size=24))

        layout.add_widget(Label(text="Usuario"))

        self.usuario_input = TextInput(hint_text="Nombre de usuario", multiline=False)
        layout.add_widget(self.usuario_input)

        layout.add_widget(Label(text="Contraseña"))

        self.password_input = TextInput(password=True, multiline=False)
        layout.add_widget(self.password_input)

        self.msg = Label(text="", color=(1,0,0,1))
        layout.add_widget(self.msg)

        btn_empleado = Button(text="Entrar como Empleado")
        btn_empleado.bind(on_press=self.login_empleado)
        layout.add_widget(btn_empleado)

        btn_patron = Button(text="Entrar como Patrón")
        btn_patron.bind(on_press=self.login_patron)
        layout.add_widget(btn_patron)

        self.add_widget(layout)

        # Cargar datos para validar
        self.store = JsonStore("data/config.json")

    def login_empleado(self, instance):
        usuario = self.usuario_input.text.strip()
        password = self.password_input.text.strip()

        if not usuario or not password:
            self.msg.text = "Por favor ingresa usuario y contraseña"
            return

        # Aquí puedes agregar validación de empleados después (de Firebase o local)
        # Por ahora solo dejamos pasar con usuario y contraseña vacíos o hardcode

        self.msg.text = "Empleado logueado correctamente"
        # Cambia a la pantalla principal o inventario cuando esté listo
        # self.manager.current = "menu"

    def login_patron(self, instance):
        usuario = self.usuario_input.text.strip()
        password = self.password_input.text.strip()

        if not usuario or not password:
            self.msg.text = "Por favor ingresa usuario y contraseña"
            return

        # Validar contraseña patrón guardada
        if self.store.exists("tienda"):
            data = self.store.get("tienda")
            if password == data.get("patron_password") and usuario == data.get("nombre"):
                self.msg.text = "Patrón logueado correctamente"
                # self.manager.current = "menu"
            else:
                self.msg.text = "Usuario o contraseña incorrectos"
        else:
            self.msg.text = "No hay tienda registrada"
