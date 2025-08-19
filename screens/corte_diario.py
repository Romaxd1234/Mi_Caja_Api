from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from pathlib import Path
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty
from kivy.clock import Clock
import json
import os
from datetime import datetime

class CorteDiario(Screen):
    nombre_usuario = StringProperty("")

    def __init__(self, **kwargs):
        super(CorteDiario, self).__init__(**kwargs)
        Clock.schedule_once(self.crear_interfaz)
        

    def crear_interfaz(self, *args):
        self.clear_widgets()
        root = RelativeLayout()


        # Fondo
        fondo = Image(source="assets/fondo.png", allow_stretch=True, keep_ratio=False)
        root.add_widget(fondo)

        # Contenedor principal
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)

        # Título
        layout.add_widget(Label(text="🧾 CORTE DIARIO", size_hint_y=None, height=40, bold=True, font_size=22))

        # Subtítulos (encabezados de la tabla)
        header = GridLayout(cols=5, size_hint_y=None, height=30, spacing=5)
        header.add_widget(Label(text="Empleado", bold=True, size_hint_y=None, height=30))
        header.add_widget(Label(text="Producto", bold=True, size_hint_y=None, height=30))
        header.add_widget(Label(text="Tipo de Venta", bold=True, size_hint_y=None, height=30))
        header.add_widget(Label(text="Total $", bold=True, size_hint_y=None, height=30))
        header.add_widget(Label(text="Hora", bold=True, size_hint_y=None, height=30))
        layout.add_widget(header)

        # Scroll con ventas, ocupa el 85% del alto disponible
        scroll = ScrollView(size_hint=(1, 0.85))
        self.ventas_layout = GridLayout(cols=5, spacing=5, size_hint_y=None)
        self.ventas_layout.bind(minimum_height=self.ventas_layout.setter('height'))
        scroll.add_widget(self.ventas_layout)
        layout.add_widget(scroll)

        # Total corte diario
        self.total_label = Label(text="TOTAL CORTE DIARIO: $0", size_hint_y=None, height=40, halign='right', valign='middle')
        self.total_label.bind(size=self.total_label.setter('text_size'))
        layout.add_widget(self.total_label)

    # Botones con altura fija 50
        botones = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_guardar = Button(text="💾 Guardar Corte", on_release=self.guardar_corte)
        btn_volver = Button(text="↩️ Volver", on_release=self.volver)
        botones.add_widget(btn_guardar)
        botones.add_widget(btn_volver)
        layout.add_widget(botones)

        root.add_widget(layout)
        self.add_widget(root)

        self.cargar_ventas()


        self.cargar_ventas()

    def cargar_ventas(self):
        self.ventas_layout.clear_widgets()
        total = 0
        hoy = datetime.now().date()

        ruta_ventas = r"C:\Users\fabiola gomey martin\Documents\APP\data\ventas.json"

        if os.path.exists(ruta_ventas):
            with open(ruta_ventas, "r", encoding="utf-8") as f:
                ventas = json.load(f)

            for venta in ventas:
                fecha_venta = datetime.strptime(venta["fecha"], "%Y-%m-%d %H:%M:%S").date()
                if fecha_venta == hoy:
                    tipo_venta = "Fuera de Inventario" if venta.get("fuera_inventario", False) else "Dentro de Inventario"

                    if venta.get("fuera_inventario", False):
                        # Sumar solo una vez el total completo de esta venta
                        total += float(venta.get("total", 0))

                    for producto in venta["productos"]:
                        self.ventas_layout.add_widget(Label(text=venta["usuario"], size_hint_y=None, height=30))

                        cantidad = int(producto.get("cantidad", 1))
                        producto_texto = f"{cantidad} x {producto.get('producto', '-')}"
                        self.ventas_layout.add_widget(Label(text=producto_texto, size_hint_y=None, height=30))

                        self.ventas_layout.add_widget(Label(text=tipo_venta, size_hint_y=None, height=30))

                        if not venta.get("fuera_inventario", False):
                            precio_unitario = float(producto.get("precio", 0))
                            subtotal = precio_unitario * cantidad
                            total += subtotal
                            self.ventas_layout.add_widget(Label(text=f"${subtotal:.2f}", size_hint_y=None, height=30))
                        else:
                            # Para fuera de inventario, solo mostrar precio (sin sumar porque ya se sumó arriba)
                            self.ventas_layout.add_widget(Label(text=f"${producto.get('precio', 0):.2f}", size_hint_y=None, height=30))

                        hora_venta = datetime.strptime(venta["fecha"], "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
                        self.ventas_layout.add_widget(Label(text=hora_venta, size_hint_y=None, height=30))

        self.total_label.text = f"TOTAL CORTE DIARIO: ${total:.2f}"


    def guardar_corte(self, instance):
        
        hoy = datetime.now().strftime("%Y-%m-%d")
        ruta_base = r"C:\Users\fabiola gomey martin\Documents\APP\data"
        ruta_cortes = os.path.join(ruta_base, "cortes")
        os.makedirs(ruta_cortes, exist_ok=True)

        archivo = os.path.join(ruta_cortes, f"corte_{hoy}.json")
        ruta_ventas = os.path.join(ruta_base, "ventas.json")

        with open(ruta_ventas, "r", encoding="utf-8") as f:
            resumen["ventas"] = [v for v in json.load(f) if v["fecha"].startswith(hoy)]

        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(resumen, f, indent=4, ensure_ascii=False)

        self.mostrar_resumen_popup(resumen)

    def mostrar_resumen_popup(self, resumen):
        from kivy.uix.popup import Popup
        contenido = BoxLayout(orientation="vertical", padding=10, spacing=10)
        contenido.add_widget(Label(text=f"✅ CORTE GUARDADO"))
        contenido.add_widget(Label(text=f"Usuario: {resumen['usuario_que_corto']}"))
        contenido.add_widget(Label(text=f"Fecha: {resumen['fecha']}"))
        contenido.add_widget(Label(text=f"Hora: {resumen['hora']}"))
        contenido.add_widget(Label(text=f"Total del día: ${resumen['total']}"))
        contenido.add_widget(Label(text="📸 Toma captura si es necesario"))

        btn_cerrar = Button(text="Cerrar", size_hint_y=None, height=40)
        contenido.add_widget(btn_cerrar)

        popup = Popup(title="Resumen del Corte", content=contenido, size_hint=(0.7, 0.6))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def volver(self, instance):
        self.manager.current = "pantalla_principal"

    def on_enter(self):
        self.cargar_ventas()


    def guardar_corte(self, instance):
        hoy = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")
        total_texto = self.total_label.text.split(": $")[-1]

        resumen = {
            "fecha": hoy,
            "hora": hora,
            "total": total_texto,
            "usuario_que_corto": self.nombre_usuario
        }

        ruta_base = Path.home() / "Documents" / "APP" / "data"
        ruta_cortes = ruta_base / "cortes"
        os.makedirs(ruta_cortes, exist_ok=True)

        archivo = ruta_cortes / f"corte_{hoy}.json"

        ruta_ventas = ruta_base / "ventas.json"
        with open(ruta_ventas, "r", encoding="utf-8") as f:
            ventas = json.load(f)

        ventas_del_dia = [v for v in ventas if v["fecha"].startswith(hoy)]
        resumen["ventas"] = ventas_del_dia

        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(resumen, f, indent=4, ensure_ascii=False)

        self.mostrar_resumen_popup(resumen)

    def mostrar_resumen_popup(self, resumen):
        from kivy.uix.popup import Popup
        contenido = BoxLayout(orientation="vertical", padding=10, spacing=10)
        contenido.add_widget(Label(text=f"✅ CORTE GUARDADO"))
        contenido.add_widget(Label(text=f"Usuario: {resumen['usuario_que_corto']}"))
        contenido.add_widget(Label(text=f"Fecha: {resumen['fecha']}"))
        contenido.add_widget(Label(text=f"Hora: {resumen['hora']}"))
        contenido.add_widget(Label(text=f"Total del día: ${resumen['total']}"))
        contenido.add_widget(Label(text="📸 Toma captura si es necesario"))

        btn_cerrar = Button(text="Cerrar", size_hint_y=None, height=40)
        contenido.add_widget(btn_cerrar)

        popup = Popup(title="Resumen del Corte", content=contenido, size_hint=(0.7, 0.6))

        def on_cerrar(instance):
            # Vaciar archivo ventas.json
            ruta_ventas = r"C:\Users\fabiola gomey martin\Documents\APP\data\ventas.json"
            with open(ruta_ventas, "w", encoding="utf-8") as f:
                f.write("[]")  # JSON vacío

            popup.dismiss()
            self.manager.current = "pantalla_principal"

        btn_cerrar.bind(on_release=on_cerrar)
        popup.open()

    def volver(self, instance):
        self.manager.current = "pantalla_principal"

    def on_enter(self):
        self.cargar_ventas()

