from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty
from kivy.resources import resource_add_path
from kivy.clock import Clock
from kivy.graphics import Rectangle
import os
import pytz
import requests
from datetime import datetime

API_URL = "https://mi-caja-api.onrender.com/tiendas"

class CorteDiario(Screen):
    nombre_usuario = StringProperty("")
    tienda_id = None  # Debe asignarse antes de abrir la ventana

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        resource_add_path(os.path.join(os.path.dirname(__file__), "assets"))

        # Fondo con canvas
        with self.canvas.before:
            self.fondo_rect = Rectangle(source="fondo.png", pos=self.pos, size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

        Clock.schedule_once(self.crear_interfaz)

    def _update_rect(self, *args):
        self.fondo_rect.pos = self.pos
        self.fondo_rect.size = self.size

    def crear_interfaz(self, *args):
        self.clear_widgets()
        root = RelativeLayout()

        # Contenedor principal
        layout = BoxLayout(orientation="vertical", padding=10, spacing=5)

        # Título
        layout.add_widget(Label(text="🧾 CORTE DIARIO", size_hint_y=None, height=35, bold=True, font_size=18))

        # Encabezados
        header = GridLayout(cols=5, size_hint_y=None, height=25, spacing=5)
        for h in ["Empleado", "Producto", "Tipo de\nVenta", "Total $", "Hora"]:
            header.add_widget(Label(text=h, bold=True, size_hint_y=None, height=25, font_size=14))
        layout.add_widget(header)

        # Scroll con ventas
        scroll = ScrollView(size_hint=(1, 0.85))
        self.ventas_layout = GridLayout(cols=5, spacing=5, size_hint_y=None)
        self.ventas_layout.bind(minimum_height=self.ventas_layout.setter('height'))
        scroll.add_widget(self.ventas_layout)
        layout.add_widget(scroll)

        # Total
        self.total_label = Label(text="TOTAL CORTE DIARIO: $0", size_hint_y=None, height=35, halign='right', valign='middle', font_size=16)
        self.total_label.bind(size=self.total_label.setter('text_size'))
        layout.add_widget(self.total_label)

        # Botones
        botones = BoxLayout(size_hint_y=None, height=45, spacing=10)
        btn_guardar = Button(text="💾 Guardar Corte", font_size=14, on_release=self.guardar_corte)
        btn_volver = Button(text="↩️ Volver", font_size=14, on_release=self.volver)
        botones.add_widget(btn_guardar)
        botones.add_widget(btn_volver)
        layout.add_widget(botones)

        root.add_widget(layout)
        self.add_widget(root)

    # --- resto del código se mantiene igual ---

    def on_enter(self):
        self.cargar_ventas()

    def cargar_ventas(self):
        self.ventas_layout.clear_widgets()
        total = 0

        if not self.tienda_id:
            self.ventas_layout.add_widget(Label(text="No se ha seleccionado la tienda.", size_hint_y=None, height=30))
            return

        try:
            resp = requests.get(f"{API_URL}/{self.tienda_id}/ventas")
            resp.raise_for_status()
            ventas = resp.json()
        except Exception as e:
            self.ventas_layout.add_widget(Label(text=f"Error al cargar ventas: {e}", size_hint_y=None, height=30))
            return

        # Zona horaria local
        zona_local = pytz.timezone("America/Mexico_City")
        hoy = datetime.now(zona_local).date()

        for venta in ventas:
            try:
                fecha_venta_utc = datetime.strptime(venta["fecha"], "%Y-%m-%d %H:%M:%S")
                fecha_venta_local = pytz.UTC.localize(fecha_venta_utc).astimezone(zona_local)
            except Exception:
                continue

            if fecha_venta_local.date() != hoy:
                continue

            tipo_venta = "Fuera de Inventario" if venta.get("fuera_inventario", False) else "Dentro de Inventario"

            for producto in venta.get("productos", []):
                cantidad = int(producto.get("cantidad", 1))
                fila_textos = [
                    venta.get("usuario", "-"),
                    f"{cantidad} x {producto.get('producto','-')}",
                    tipo_venta,
                    f"${float(producto.get('precio',0))*cantidad:.2f}",
                    fecha_venta_local.strftime("%H:%M:%S")
                ]
                for texto in fila_textos:
                    lbl = Label(
                        text=texto,
                        size_hint_y=None,
                        height=50,
                        halign='center',
                        valign='middle'
                    )
                    lbl.bind(size=lbl.setter('text_size'))
                    self.ventas_layout.add_widget(lbl)

                total += float(producto.get("precio",0)) * cantidad

        self.total_label.text = f"TOTAL CORTE DIARIO: ${total:.2f}"

    def set_tienda_id(self, tienda_id, nombre_usuario):
        self.tienda_id = tienda_id
        self.nombre_usuario = nombre_usuario
        self.cargar_ventas() 

    def guardar_corte(self, instance):
        if not self.tienda_id or not self.nombre_usuario:
            self.mostrar_popup("Error", "No se ha seleccionado la tienda o usuario")
            return

        try:
            total = float(self.total_label.text.split(": $")[-1])
        except:
            total = 0

        # 🔹 Generar fecha/hora local de Ciudad de México
        zona_local = pytz.timezone("America/Mexico_City")
        fecha_hora_local = datetime.now(zona_local).strftime("%Y-%m-%d %H:%M:%S")

        try:
            # 🔹 Enviar fecha/hora local al backend
            resp = requests.post(
                f"{API_URL}/{self.tienda_id}/cortes/diarios",
                params={
                    "usuario_que_corto": self.nombre_usuario,
                    "fecha_corte": fecha_hora_local
                }
            )
            resp.raise_for_status()
            resumen = resp.json()
        except Exception as e:
            self.mostrar_popup("Error", f"No se pudo guardar corte: {e}")
            return

        try:
            resp = requests.delete(f"{API_URL}/{self.tienda_id}/ventas/")
            resp.raise_for_status()
        except Exception as e:
            print(f"Error borrando ventas: {e}")

        self.mostrar_resumen_popup(resumen)

    def mostrar_resumen_popup(self, resumen):
        contenido = BoxLayout(orientation="vertical", padding=10, spacing=10)

        contenido.add_widget(Label(text="✅ CORTE GUARDADO"))
        contenido.add_widget(Label(text=f"Usuario: {resumen['usuario_que_corto']}"))

        # Mostrar fecha/hora local
        zona_local = pytz.timezone("America/Mexico_City")
        fecha_hora_local = datetime.now(zona_local).strftime("%d/%m/%Y %H:%M:%S")
        contenido.add_widget(Label(text=f"Fecha: {fecha_hora_local.split(' ')[0]}"))
        contenido.add_widget(Label(text=f"Hora: {fecha_hora_local.split(' ')[1]}"))

        contenido.add_widget(Label(text=f"Total del día: ${resumen['total']}"))
        contenido.add_widget(Label(text="📸 Toma captura si es necesario"))

        btn_cerrar = Button(text="Cerrar", size_hint_y=None, height=40)
        contenido.add_widget(btn_cerrar)

        popup = Popup(title="Resumen del Corte", content=contenido, size_hint=(0.7, 0.6))

        def cerrar_popup(instance):
            popup.dismiss()
            self.manager.current = "pantalla_principal"

        btn_cerrar.bind(on_release=cerrar_popup)
        popup.open()

    def mostrar_popup(self, titulo, mensaje):
        contenido = BoxLayout(orientation='vertical', padding=10, spacing=10)
        contenido.add_widget(Label(text=mensaje))
        btn_cerrar = Button(text="Cerrar", size_hint_y=None, height=40)
        contenido.add_widget(btn_cerrar)
        popup = Popup(title=titulo, content=contenido, size_hint=(0.6, 0.4))
        btn_cerrar.bind(on_release=popup.dismiss)
        popup.open()

    def volver(self, instance):
        self.manager.current = "pantalla_principal"
