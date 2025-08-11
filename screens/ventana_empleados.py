from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.storage.jsonstore import JsonStore
import os

class VentanaEmpleados(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        from kivy.uix.image import Image
        fondo = Image(source=r'C:/Users/fabiola gomey martin/Documents/APP/assets/fondo.png',
                      allow_stretch=True, keep_ratio=False,
                      size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self.layout.add_widget(fondo)

        self.contenedor = BoxLayout(orientation='vertical', padding=20, spacing=10,
                                    size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.layout.add_widget(self.contenedor)

        # Botones arriba: agregar, editar, eliminar, notas
        botones_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        self.contenedor.add_widget(botones_layout)

        self.btn_agregar = Button(text="Agregar Empleado")
        self.btn_editar = Button(text="Editar Empleado")
        self.btn_eliminar = Button(text="Eliminar Empleado")
        self.btn_prestamos = Button(text="Préstamos")
        self.btn_notas = Button(text="Notas")

        botones_layout.add_widget(self.btn_agregar)
        botones_layout.add_widget(self.btn_editar)
        botones_layout.add_widget(self.btn_eliminar)
        botones_layout.add_widget(self.btn_prestamos)
        botones_layout.add_widget(self.btn_notas)

        # Selector de empleados
        seleccion_layout = BoxLayout(size_hint=(1, None), height=40, spacing=10)
        self.contenedor.add_widget(seleccion_layout)

        seleccion_layout.add_widget(Label(text="Empleado:", size_hint=(None, 1), width=80))

        self.spinner_empleados = Spinner(text="Selecciona empleado", values=[], size_hint=(1, 1))
        seleccion_layout.add_widget(self.spinner_empleados)

        # Área para mostrar info del empleado
        self.empleados_layout = BoxLayout(orientation='vertical', spacing=10)
        self.contenedor.add_widget(self.empleados_layout)

        # Botón Volver abajo izquierda
        self.btn_volver = Button(text="Volver", size_hint=(0.2, None), height=40,
                                 pos_hint={'x': 0.02, 'y': 0.02})
        self.layout.add_widget(self.btn_volver)

        # Bindings
        self.btn_volver.bind(on_release=self.volver)
        self.btn_notas.bind(on_release=self.abrir_popup_notas)
        self.btn_agregar.bind(on_release=self.abrir_popup_agregar)
        self.btn_editar.bind(on_release=self.abrir_popup_editar)
        self.btn_eliminar.bind(on_release=self.eliminar_empleado)
        self.btn_prestamos.bind(on_release=self.abrir_popup_prestamo)
        self.spinner_empleados.bind(text=self.mostrar_info_empleado)

        # Variables para datos
        self.ruta_tienda = None
        self.empleados = []

    def set_ruta_tienda(self, ruta):
        self.ruta_tienda = ruta
        self.cargar_empleados()

    def cargar_empleados(self):
        self.empleados_layout.clear_widgets()
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            return

        store = JsonStore(self.ruta_tienda)
        if not store.exists("empleados"):
            self.empleados = []
        else:
            self.empleados = store.get("empleados").get("lista", [])

        # Actualizar spinner
        nombres = [emp.get('nombre', '') for emp in self.empleados]
        if nombres:
            self.spinner_empleados.values = nombres
            self.spinner_empleados.text = nombres[0]
        else:
            self.spinner_empleados.values = []
            self.spinner_empleados.text = "No hay empleados"

        # Mostrar info del empleado seleccionado
        self.mostrar_info_empleado(self.spinner_empleados, self.spinner_empleados.text)

    def mostrar_info_empleado(self, spinner, texto):
        self.empleados_layout.clear_widgets()
        emp = next((e for e in self.empleados if e.get('nombre') == texto), None)
        if not emp:
            self.empleados_layout.add_widget(Label(text="Seleccione un empleado"))
            return

        texto_info = f"Nombre: {emp.get('nombre', '')}\nPuesto: {emp.get('puesto', '')}\nSueldo: {emp.get('sueldo', '')}\nNota: {emp.get('nota', '')}"
        self.empleados_layout.add_widget(Label(text=texto_info, color=(0, 0, 0, 1)))

    def abrir_popup_agregar(self, instance):
        self.popup_editar_agregar("Agregar Empleado")

    def abrir_popup_editar(self, instance):
        if not self.empleados:
            self.mostrar_popup("Aviso", "No hay empleados para editar.")
            return
        self.popup_editar_agregar("Editar Empleado", editar=True)

    def popup_editar_agregar(self, titulo, editar=False):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        input_nombre = TextInput(hint_text="Nombre", multiline=False)
        input_puesto = TextInput(hint_text="Puesto", multiline=False)
        input_sueldo = TextInput(hint_text="Sueldo", multiline=False)
        
        # Campo contraseña con ojito
        box_password = BoxLayout(size_hint_y=None, height=40, spacing=5)
        input_password = TextInput(hint_text="Contraseña", multiline=False, password=True)
        btn_ojito = Button(text="👁️", size_hint=(None, 1), width=40)

        def toggle_password(instance):
            input_password.password = not input_password.password

        btn_ojito.bind(on_release=toggle_password)
        box_password.add_widget(input_password)
        box_password.add_widget(btn_ojito)

        # Leyenda
        leyenda = Label(
            text="[i]Esta contraseña la debe teclear el usuario y sólo él tendrá acceso a ella.[/i]",
            markup=True,
            font_size=12,
            size_hint_y=None,
            height=30,
            halign='center'
        )
        leyenda.bind(size=leyenda.setter('text_size'))

        input_nota = TextInput(hint_text="Nota", multiline=True, size_hint_y=None, height=80)

        if editar:
            nombre_emp = self.spinner_empleados.text
            emp = next((e for e in self.empleados if e.get('nombre') == nombre_emp), None)
            if emp:
                input_nombre.text = emp.get('nombre', '')
                input_puesto.text = emp.get('puesto', '')
                input_sueldo.text = str(emp.get('sueldo', ''))
                input_nota.text = emp.get('nota', '')
                input_password.text = emp.get('password', '')  # si guardas la contraseña

        contenido.add_widget(input_nombre)
        contenido.add_widget(input_puesto)
        contenido.add_widget(input_sueldo)
        contenido.add_widget(box_password)
        contenido.add_widget(leyenda)
        contenido.add_widget(input_nota)

        btn_guardar = Button(text="Guardar", size_hint=(1, None), height=40)
        contenido.add_widget(btn_guardar)

        popup = Popup(title=titulo, content=contenido, size_hint=(0.7, 0.8))

        def guardar(instance):
            nombre = input_nombre.text.strip()
            puesto = input_puesto.text.strip()
            sueldo = input_sueldo.text.strip()
            nota = input_nota.text.strip()
            password = input_password.text.strip()

            if not nombre:
                self.mostrar_popup("Error", "El nombre es obligatorio.")
                return

            if editar:
                for e in self.empleados:
                    if e.get('nombre') == self.spinner_empleados.text:
                        e['nombre'] = nombre
                        e['puesto'] = puesto
                        e['sueldo'] = sueldo
                        e['nota'] = nota
                        e['password'] = password
                        break
            else:
                self.empleados.append({
                    'nombre': nombre,
                    'puesto': puesto,
                    'sueldo': sueldo,
                    'nota': nota,
                    'password': password
                })

            self.guardar_empleados_en_json()
            self.cargar_empleados()
            popup.dismiss()

        btn_guardar.bind(on_release=guardar)
        popup.open()

    def eliminar_empleado(self, instance):
        if not self.empleados:
            self.mostrar_popup("Aviso", "No hay empleados para eliminar.")
            return
        nombre_emp = self.spinner_empleados.text
        if not nombre_emp or nombre_emp == "No hay empleados":
            self.mostrar_popup("Aviso", "Seleccione un empleado para eliminar.")
            return

        def confirmar_eliminar(instance):
            self.empleados = [e for e in self.empleados if e.get('nombre') != nombre_emp]
            self.guardar_empleados_en_json()
            self.cargar_empleados()
            popup.dismiss()

        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        contenido.add_widget(Label(text=f"¿Eliminar empleado '{nombre_emp}'?"))
        btn_si = Button(text="Sí", size_hint=(1, None), height=40)
        btn_no = Button(text="No", size_hint=(1, None), height=40)
        botones = BoxLayout(spacing=10)
        botones.add_widget(btn_si)
        botones.add_widget(btn_no)
        contenido.add_widget(botones)

        popup = Popup(title="Confirmar eliminación", content=contenido, size_hint=(0.6, 0.4))
        btn_si.bind(on_release=confirmar_eliminar)
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def abrir_popup_notas(self, instance):
        if not self.empleados:
            self.mostrar_popup("Aviso", "No hay empleados para agregar notas.")
            return

        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        spinner_empleados = Spinner(
            text=self.empleados[0]['nombre'],
            values=[emp['nombre'] for emp in self.empleados],
            size_hint=(1, None),
            height=44
        )
        contenido.add_widget(Label(text="Selecciona empleado:"))
        contenido.add_widget(spinner_empleados)

        input_nota = TextInput(text="", multiline=True, size_hint=(1, None), height=100, hint_text="Escribe la nota aquí")
        contenido.add_widget(Label(text="Nota:"))
        contenido.add_widget(input_nota)

        btn_guardar = Button(text="Guardar", size_hint=(1, None), height=40)
        contenido.add_widget(btn_guardar)

        popup = Popup(title="Notas de Empleado", content=contenido, size_hint=(0.7, 0.6))

        def cargar_nota_empleado(spinner, text):
            for emp in self.empleados:
                if emp['nombre'] == text:
                    input_nota.text = emp.get('nota', '')
                    break

        spinner_empleados.bind(text=cargar_nota_empleado)

        def guardar_nota(instance):
            nombre_emp = spinner_empleados.text
            nota = input_nota.text.strip()
            for emp in self.empleados:
                if emp['nombre'] == nombre_emp:
                    emp['nota'] = nota
                    break
            self.guardar_empleados_en_json()
            self.cargar_empleados()
            popup.dismiss()

        btn_guardar.bind(on_release=guardar_nota)
        cargar_nota_empleado(spinner_empleados, spinner_empleados.text)
        popup.open()

    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)
        contenido.add_widget(Label(text=mensaje))
        btn_cerrar = Button(text="Cerrar", size_hint=(1, None), height=40)
        contenido.add_widget(btn_cerrar)
        popup = Popup(title=titulo, content=contenido, size_hint=(0.6, 0.4))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def guardar_empleados_en_json(self):
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            return
        store = JsonStore(self.ruta_tienda)
        store.put("empleados", lista=self.empleados)

    def volver(self, instance):
        self.manager.current = "pantalla_principal"

    def abrir_popup_prestamo(self, instance):
        contenido = BoxLayout(orientation='vertical', spacing=10, padding=10)

        label = Label(text='Préstamo a empleado')
        self.input_cantidad = TextInput(hint_text='Cantidad', input_filter='float', multiline=False)

        btn_hacer_prestamo = Button(text='Hacer préstamo')
        btn_hacer_prestamo.bind(on_release=self.hacer_prestamo)

        contenido.add_widget(label)
        contenido.add_widget(self.input_cantidad)
        contenido.add_widget(btn_hacer_prestamo)

        self.popup_prestamo = Popup(title='Nuevo préstamo', content=contenido,
                                    size_hint=(0.8, 0.5), auto_dismiss=True)
        self.popup_prestamo.open()

    def hacer_prestamo(self, instance):
        cantidad = self.input_cantidad.text.strip()
        nombre_emp = self.spinner_empleados.text
        if cantidad and nombre_emp and nombre_emp != "No hay empleados":
            mensaje = f"Se le ha realizado un préstamo de ${cantidad} a {nombre_emp}"
            pantalla_principal = self.manager.get_screen("pantalla_principal")
            pantalla_principal.mostrar_alerta_prestamo(mensaje)
            self.guardar_prestamo_en_tienda(nombre_emp, cantidad)
        self.popup_prestamo.dismiss()


    def guardar_prestamo_en_tienda(self, nombre_emp, cantidad):
        if not self.ruta_tienda or not os.path.exists(self.ruta_tienda):
            return
        store = JsonStore(self.ruta_tienda)

        if not store.exists("empleados"):
            return
    
        empleados = store.get("empleados").get("lista", [])
        for emp in empleados:
            if emp.get("nombre") == nombre_emp:
                emp["prestamo"] = {
                    "cantidad": str(cantidad),
                    "mensaje": f"Se te ha realizado un préstamo de ${cantidad}",
                    "pendiente": True
                }

                break

        store.put("empleados", lista=empleados)