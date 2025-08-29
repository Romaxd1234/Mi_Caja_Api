from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window  # <-- Import necesario
import os

from screens.bienvenida import BienvenidaScreen
from screens.seleccion_rol import SeleccionRolScreen
from screens.abrir_tienda import AbrirTiendaScreen
from screens.pantalla_patron import PantallaPatronScreen
from screens.login_patron import LoginPatronScreen
from screens.pantalla_principal import VentanaPrincipal  # IMPORTA LA CLASE CORRECTA
from screens.ventana_empleados import VentanaEmpleados
from screens.login_empleado import LoginEmpleadoScreen
from screens.pantalla_inventario import VentanaInventario
from screens.venta_inventario import VentaInventario
from screens.corte_diario import CorteDiario
from screens.registro_cortes import RegistroCortes
from screens.corte_semanal import CorteSemanalScreen
from screens.registro_semanal import RegistroSemanal

class MiCajaApp(App):
    def build(self):

        sm = ScreenManager()

        # Agregamos todas las pantallas
        sm.add_widget(BienvenidaScreen(name="bienvenida"))
        sm.add_widget(SeleccionRolScreen(name="seleccion_rol"))
        sm.add_widget(AbrirTiendaScreen(name="abrir_tienda"))
        sm.add_widget(PantallaPatronScreen(name="pantalla_patron"))
        sm.add_widget(LoginPatronScreen(name='login_patron'))
        sm.add_widget(VentanaPrincipal(name='pantalla_principal'))
        sm.add_widget(VentanaEmpleados(name="ventana_empleados"))
        sm.add_widget(LoginEmpleadoScreen(name='login_empleado'))
        sm.add_widget(VentanaInventario(name='inventario'))
        sm.add_widget(VentaInventario(name='venta_inventario'))
        sm.add_widget(CorteDiario(name="corte_diario"))
        sm.add_widget(RegistroCortes(name='registro_cortes'))
        sm.add_widget(CorteSemanalScreen(name="corte_semanal"))
        sm.add_widget(RegistroSemanal(name="registro_semanal"))

        # Controlamos la pantalla inicial según exista o no la config
        if not os.path.exists("data/config.json"):
            sm.current = "bienvenida"
        else:
            sm.current = "abrir_tienda"

        return sm

if __name__ == "__main__":
    MiCajaApp().run()
