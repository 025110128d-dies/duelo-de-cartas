from ursina import *
from ursina import curve
import math
import random

class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None

class ListaCircular:
    def __init__(self):
        self.cola = None

    @property
    def cabeza(self):
        if self.cola is None:
            return None
        return self.cola.siguiente

    def esta_vacia(self):
        return self.cola is None

    def insertar_inicio(self, dato):
        nuevo = Nodo(dato)
        if self.cola is None:
            nuevo.siguiente = nuevo
            self.cola = nuevo
        else:
            nuevo.siguiente = self.cola.siguiente
            self.cola.siguiente = nuevo

    def insertar_final(self, dato):
        nuevo = Nodo(dato)
        if self.cola is None:
            nuevo.siguiente = nuevo
            self.cola = nuevo
            return
        nuevo.siguiente = self.cola.siguiente
        self.cola.siguiente = nuevo
        self.cola = nuevo

    def recorrer(self):
        if self.cola is None:
            return []
        resultado = []
        inicio = self.cola.siguiente
        actual = inicio
        while True:
            resultado.append(actual.valor)
            actual = actual.siguiente
            if actual is inicio:
                break
        return resultado

    def contiene(self, buscado):
        if self.cola is None:
            return False
        inicio = self.cola.siguiente
        actual = inicio
        while True:
            if actual.valor == buscado:
                return True
            actual = actual.siguiente
            if actual is inicio:
                break
        return False

    def eliminar_inicio(self):
        if self.cola is None:
            raise IndexError("La lista circular está vacía")
        cabeza = self.cola.siguiente
        dato = cabeza.valor
        if cabeza is self.cola:
            self.cola = None
        else:
            self.cola.siguiente = cabeza.siguiente
        return dato

    def eliminar(self, buscado):
        if self.cola is None:
            return False
        anterior = self.cola
        actual = self.cola.siguiente
        inicio = actual
        while True:
            if actual.valor == buscado:
                if actual is anterior:
                    self.cola = None
                else:
                    anterior.siguiente = actual.siguiente
                    if actual is self.cola:
                        self.cola = anterior
                return True
            anterior = actual
            actual = actual.siguiente
            if actual is inicio:
                break
        return False


# ==========================================
# CONFIGURACIÓN Y CONSTANTES DEL JUEGO
# ==========================================
CARTAS_INFO = {
    'FUEGO': {'color': color.red, 'simbolo': '🔥'},
    'AGUA': {'color': color.blue, 'simbolo': '💧'},
    'TIERRA': {'color': color.rgb(101, 67, 33), 'simbolo': '⛰️'}, # Marrón
    'AIRE': {'color': color.violet, 'simbolo': '💨'},
    'RAYO': {'color': color.yellow, 'simbolo': '⚡'}
}

# Reglas: Clave vence a Valor
REGLAS_COMBATE = {
    'FUEGO': 'AIRE',
    'AIRE': 'TIERRA',
    'TIERRA': 'RAYO',
    'RAYO': 'AGUA',
    'AGUA': 'FUEGO'
}

# ==========================================
# ENTIDADES 3D
# ==========================================
class Carta3D(Entity):
    def __init__(self, tipo, posicion, es_interactiva=False, callback=None, **kwargs):
        super().__init__(
            model='cube',
            scale=(1.5, 2.2, 0.1),
            position=posicion,
            color=CARTAS_INFO[tipo]['color'],
            collider='box' if es_interactiva else None,
            **kwargs
        )
        self.tipo = tipo
        self.callback = callback
        self.es_interactiva = es_interactiva
        
        # Borde brillante
        self.borde = Entity(parent=self, model='cube', scale=(1.05, 1.05, 0.5), color=color.white33, z=0.01)
        
        # Símbolo y Texto
        self.texto_simbolo = Text(parent=self, text=CARTAS_INFO[tipo]['simbolo'], scale=10, z=-0.6, origin=(0, 0), color=color.white)
        self.texto_nombre = Text(parent=self, text=tipo, scale=3, z=-0.6, y=-0.35, origin=(0, 0), color=color.white)

    def on_mouse_enter(self):
        if self.es_interactiva:
            self.animate_position(self.position + Vec3(0, 0.5, -0.5), duration=0.2)
            self.borde.color = color.cyan

    def on_mouse_exit(self):
        if self.es_interactiva:
            self.animate_position(self.position - Vec3(0, 0.5, -0.5), duration=0.2)
            self.borde.color = color.white33

    def on_click(self):
        if self.es_interactiva and self.callback:
            self.callback(self)


class Conexion3D(Entity):
    def __init__(self, p1, p2):
        super().__init__(model='cube', color=color.cyan)
        self.position = (p1 + p2) / 2
        self.look_at(p2)
        distancia = distance(p1, p2)
        self.scale = (0.05, 0.05, distancia - 1.5)


# ==========================================
# CONTROLADOR PRINCIPAL
# ==========================================
class JuegoCartas:
    def __init__(self):
        self.app = Ursina()
        window.title = "DUELO DE CARTAS: LISTA CIRCULAR 3D"
        window.borderless = False
        window.fullscreen = False
        window.color = color.rgb(10, 10, 15) # Fondo oscuro

        # Luces y cámara
        self.luz = DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))
        camera.position = (0, 5, -15)
        camera.look_at(Vec3(0, 0, 0))

        # Variables del juego
        self.lista_cartas = ListaCircular()
        self.inicializar_lista()
        
        self.vidas_jugador = 3
        self.vidas_rival = 3
        self.puntuacion = 0
        self.ronda = 1
        
        self.estado_actual = "MENU"
        self.escena_entidades = []
        self.ui_elementos = []
        self.nodo_actual_recorrido = None
        
        self.crear_interfaz()
        self.mostrar_menu_principal()

        # Entrada de teclado global
        window.input = self.manejar_teclas

    def manejar_teclas(self, key):
        if key == 'escape':
            if self.estado_actual != "MENU":
                self.limpiar_escena()
                self.mostrar_menu_principal()
        
        if self.estado_actual == "LISTA" and not self.lista_cartas.esta_vacia():
            if key == 'n': # Siguiente nodo
                if self.nodo_actual_recorrido is None:
                    self.nodo_actual_recorrido = self.lista_cartas.cabeza
                else:
                    self.nodo_actual_recorrido = self.nodo_actual_recorrido.siguiente
                self.renderizar_lista_circular()
            elif key == 'b': # Anterior nodo (simulado buscando el previo)
                if self.nodo_actual_recorrido is not None:
                    actual = self.lista_cartas.cabeza
                    while actual.siguiente is not self.nodo_actual_recorrido:
                        actual = actual.siguiente
                    self.nodo_actual_recorrido = actual
                    self.renderizar_lista_circular()
            elif key == 'e': # Interactuar
                if self.nodo_actual_recorrido:
                    print(f"Interactuado con: {self.nodo_actual_recorrido.valor}")

    def inicializar_lista(self):
        self.lista_cartas = ListaCircular()
        for tipo in ['FUEGO', 'AGUA', 'TIERRA', 'AIRE', 'RAYO']:
            self.lista_cartas.insertar_final(tipo)

    def limpiar_escena(self):
        for e in self.escena_entidades:
            destroy(e)
        self.escena_entidades.clear()
        
        for ui in self.ui_elementos:
            ui.enabled = False

    def registrar_ui(self, elemento):
        self.ui_elementos.append(elemento)
        return elemento

    def crear_interfaz(self):
        # --- MENÚ PRINCIPAL ---
        self.panel_menu = self.registrar_ui(Entity(parent=camera.ui, enabled=False))
        Text(parent=self.panel_menu, text="DUELO DE CARTAS\nLISTA CIRCULAR 3D", origin=(0,0), y=0.3, scale=3, color=color.cyan)
        
        Button(parent=self.panel_menu, text="1. Jugar", y=0.1, scale=(0.4, 0.08), color=color.dark_gray, on_click=self.iniciar_juego)
        Button(parent=self.panel_menu, text="2. Ver Lista Circular", y=0.0, scale=(0.4, 0.08), color=color.dark_gray, on_click=self.mostrar_lista_circular)
        Button(parent=self.panel_menu, text="3. Administrar Cartas", y=-0.1, scale=(0.4, 0.08), color=color.dark_gray, on_click=self.mostrar_admin)
        Button(parent=self.panel_menu, text="4. Instrucciones", y=-0.2, scale=(0.4, 0.08), color=color.dark_gray, on_click=self.mostrar_instrucciones)
        Button(parent=self.panel_menu, text="5. Reiniciar Partida", y=-0.3, scale=(0.4, 0.08), color=color.dark_gray, on_click=self.reiniciar_partida)
        Button(parent=self.panel_menu, text="6. Salir", y=-0.4, scale=(0.4, 0.08), color=color.red, on_click=application.quit)

        # --- HUD JUEGO ---
        self.hud_juego = self.registrar_ui(Entity(parent=camera.ui, enabled=False))
        self.txt_estado = Text(parent=self.hud_juego, text="", origin=(0, 0), y=0.4, scale=2, color=color.yellow)
        self.txt_stats = Text(parent=self.hud_juego, text="", origin=(-0.5, 0.5), x=-0.85, y=0.45, scale=1.5, color=color.white)
        Button(parent=self.hud_juego, text="Volver al Menú (ESC)", origin=(0.5, 0.5), x=0.85, y=0.48, scale=(0.25, 0.05), color=color.red, on_click=self.mostrar_menu_principal)

        # --- ADMINISTRACIÓN ---
        self.panel_admin = self.registrar_ui(Entity(parent=camera.ui, enabled=False))
        Text(parent=self.panel_admin, text="ADMINISTRAR LISTA CIRCULAR", origin=(0,0), y=0.4, scale=2, color=color.cyan)
        
        self.input_carta = InputField(parent=self.panel_admin, y=0.2, text="FUEGO")
        
        Button(parent=self.panel_admin, text="Insertar Inicio", y=0.1, x=-0.2, scale=(0.3, 0.08), color=color.dark_gray, on_click=lambda: self.admin_accion('ins_ini'))
        Button(parent=self.panel_admin, text="Insertar Final", y=0.1, x=0.2, scale=(0.3, 0.08), color=color.dark_gray, on_click=lambda: self.admin_accion('ins_fin'))
        Button(parent=self.panel_admin, text="Buscar", y=0.0, x=-0.2, scale=(0.3, 0.08), color=color.dark_gray, on_click=lambda: self.admin_accion('buscar'))
        Button(parent=self.panel_admin, text="Eliminar Inicio", y=0.0, x=0.2, scale=(0.3, 0.08), color=color.dark_gray, on_click=lambda: self.admin_accion('elim_ini'))
        Button(parent=self.panel_admin, text="Eliminar Específica", y=-0.1, x=0, scale=(0.3, 0.08), color=color.dark_gray, on_click=lambda: self.admin_accion('elim_esp'))
        
        self.txt_admin_log = Text(parent=self.panel_admin, text="", origin=(0,0), y=-0.3, scale=1.5, color=color.yellow)
        Button(parent=self.panel_admin, text="Volver", y=-0.45, scale=(0.3, 0.08), color=color.red, on_click=self.mostrar_menu_principal)

        # --- INSTRUCCIONES ---
        self.panel_inst = self.registrar_ui(Entity(parent=camera.ui, enabled=False))
        instrucciones_txt = """
        INSTRUCCIONES
        
        COMBATE:
        - FUEGO vence a AIRE
        - AIRE vence a TIERRA
        - TIERRA vence a RAYO
        - RAYO vence a AGUA
        - AGUA vence a FUEGO
        
        LISTA CIRCULAR:
        Presiona N para avanzar al siguiente nodo.
        Presiona B para retroceder.
        La lista es infinita, el último nodo conecta con el primero.
        """
        Text(parent=self.panel_inst, text=instrucciones_txt, origin=(0,0), y=0.1, scale=1.5)
        Button(parent=self.panel_inst, text="Volver", y=-0.4, scale=(0.3, 0.08), color=color.red, on_click=self.mostrar_menu_principal)

    def mostrar_menu_principal(self):
        self.limpiar_escena()
        self.estado_actual = "MENU"
        self.panel_menu.enabled = True
        camera.position = (0, 5, -15)
        camera.look_at(Vec3(0,0,0))

    def mostrar_instrucciones(self):
        self.limpiar_escena()
        self.estado_actual = "INSTRUCCIONES"
        self.panel_inst.enabled = True

    def reiniciar_partida(self):
        self.vidas_jugador = 3
        self.vidas_rival = 3
        self.puntuacion = 0
        self.ronda = 1
        self.inicializar_lista()
        self.mostrar_menu_principal()

    def actualizar_hud_juego(self):
        self.txt_stats.text = f"Ronda: {self.ronda}\nJugador: {'❤️'*self.vidas_jugador}\nRival: {'❤️'*self.vidas_rival}\nPuntos: {self.puntuacion}"

    # ==========================================
    # LÓGICA DE COMBATE
    # ==========================================
    def iniciar_juego(self):
        if self.lista_cartas.esta_vacia():
            self.txt_estado.text = "¡La lista de cartas está vacía! Añade cartas."
            self.hud_juego.enabled = True
            return

        self.limpiar_escena()
        self.estado_actual = "JUGAR"
        self.hud_juego.enabled = True
        self.txt_estado.text = "Selecciona una carta"
        self.actualizar_hud_juego()

        # Mesa
        mesa = Entity(model='cube', scale=(20, 0.5, 15), color=color.rgb(30, 30, 40), position=(0, -1, 0))
        self.escena_entidades.append(mesa)

        # Cartas del jugador basadas en la lista circular
        cartas_disponibles = self.lista_cartas.recorrer()
        # Limitamos a mostrar máximo 7 para no saturar la pantalla
        cartas_mostrar = cartas_disponibles[:7] 
        
        ancho_total = len(cartas_mostrar) * 2
        inicio_x = -ancho_total / 2 + 1

        for i, tipo in enumerate(cartas_mostrar):
            carta = Carta3D(
                tipo=tipo,
                posicion=(inicio_x + i * 2, 0, -5),
                es_interactiva=True,
                callback=self.jugar_ronda,
                rotation=(30, 0, 0)
            )
            self.escena_entidades.append(carta)

    def jugar_ronda(self, carta_jugador):
        # Desactivar interactividad
        for e in self.escena_entidades:
            if isinstance(e, Carta3D):
                e.es_interactiva = False

        # Animación jugador
        carta_jugador.animate_position((0, 1, -2), duration=0.5, curve=curve.out_back)
        carta_jugador.animate_rotation((0, 0, 0), duration=0.5)

        # Elección del rival
        opciones_rival = list(CARTAS_INFO.keys())
        tipo_rival = random.choice(opciones_rival)
        
        carta_rival = Carta3D(
            tipo=tipo_rival,
            posicion=(0, 1, 5),
            es_interactiva=False,
            rotation=(0, 180, 0)
        )
        self.escena_entidades.append(carta_rival)
        carta_rival.animate_position((0, 1, 2), duration=0.5, curve=curve.out_back)
        carta_rival.animate_rotation((0, 0, 0), duration=0.5)

        invoke(self.resolver_combate, carta_jugador.tipo, tipo_rival, delay=1.5)

    def resolver_combate(self, tipo_jugador, tipo_rival):
        if tipo_jugador == tipo_rival:
            resultado = "EMPATE"
        elif REGLAS_COMBATE.get(tipo_jugador) == tipo_rival:
            resultado = "¡GANASTE LA RONDA!"
            self.puntuacion += 10
            self.vidas_rival -= 1
        else:
            resultado = "PERDISTE LA RONDA"
            self.vidas_jugador -= 1

        self.txt_estado.text = f"{tipo_jugador} vs {tipo_rival}\n{resultado}"
        self.ronda += 1
        self.actualizar_hud_juego()

        if self.vidas_jugador <= 0:
            invoke(self.mostrar_fin_juego, False, delay=2)
        elif self.vidas_rival <= 0:
            invoke(self.mostrar_fin_juego, True, delay=2)
        else:
            invoke(self.iniciar_juego, delay=2)

    def mostrar_fin_juego(self, victoria):
        self.limpiar_escena()
        self.estado_actual = "FIN"
        self.hud_juego.enabled = False
        
        mensaje = "¡VICTORIA!" if victoria else "DERROTA..."
        color_msj = color.green if victoria else color.red
        
        panel_fin = self.registrar_ui(Entity(parent=camera.ui))
        Text(parent=panel_fin, text=mensaje, origin=(0,0), y=0.2, scale=4, color=color_msj)
        Text(parent=panel_fin, text=f"Puntuación Final: {self.puntuacion}\nRondas: {self.ronda}", origin=(0,0), y=0, scale=2)
        
        Button(parent=panel_fin, text="Volver al Menú", y=-0.3, scale=(0.4, 0.08), color=color.dark_gray, on_click=self.mostrar_menu_principal)


    # ==========================================
    # VISUALIZACIÓN DE LISTA CIRCULAR 3D
    # ==========================================
    def mostrar_lista_circular(self):
        self.limpiar_escena()
        self.estado_actual = "LISTA"
        
        self.hud_vista = self.registrar_ui(Entity(parent=camera.ui))
        Text(parent=self.hud_vista, text="LISTA CIRCULAR ENLAZADA\nN: Siguiente | B: Anterior | ESC: Menú", origin=(0,0), y=0.45, scale=1.5, color=color.cyan)
        
        camera.position = (0, 10, -15)
        camera.look_at(Vec3(0, 0, 0))

        if not self.lista_cartas.esta_vacia():
            self.nodo_actual_recorrido = self.lista_cartas.cabeza
            self.renderizar_lista_circular()
        else:
            Text(parent=self.hud_vista, text="La lista está vacía", origin=(0,0), scale=2, color=color.red)

    def renderizar_lista_circular(self):
        # Limpiar solo entidades 3D
        for e in self.escena_entidades:
            destroy(e)
        self.escena_entidades.clear()

        cartas = self.lista_cartas.recorrer()
        if not cartas: return

        num_cartas = len(cartas)
        radio = max(4, num_cartas * 0.8)
        
        nodos_visuales = []
        
        for i, tipo in enumerate(cartas):
            angulo = i * (2 * math.pi / num_cartas)
            x = math.cos(angulo) * radio
            z = math.sin(angulo) * radio
            
            es_activo = self.nodo_actual_recorrido and self.nodo_actual_recorrido.valor == tipo
            
            carta = Carta3D(
                tipo=tipo,
                posicion=(x, 0, z),
                rotation=(30, -math.degrees(angulo) - 90, 0)
            )
            
            if es_activo:
                carta.animate_position((x, 1, z), duration=0.5, loop=True)
                carta.borde.color = color.green
            
            self.escena_entidades.append(carta)
            nodos_visuales.append(carta.position)

        # Dibujar conexiones
        for i in range(num_cartas):
            p1 = nodos_visuales[i]
            p2 = nodos_visuales[(i + 1) % num_cartas] # Conexión circular
            conexion = Conexion3D(p1, p2)
            self.escena_entidades.append(conexion)

    # ==========================================
    # ADMINISTRACIÓN DE LA ESTRUCTURA
    # ==========================================
    def mostrar_admin(self):
        self.limpiar_escena()
        self.estado_actual = "ADMIN"
        self.panel_admin.enabled = True
        self.txt_admin_log.text = ""
        self.mostrar_lista_circular_mini()

    def mostrar_lista_circular_mini(self):
        # Muestra una versión pequeña para ver cambios en vivo
        for e in self.escena_entidades:
            destroy(e)
        self.escena_entidades.clear()
        
        camera.position = (0, 8, -12)
        camera.look_at(Vec3(0, 0, 0))
        
        cartas = self.lista_cartas.recorrer()
        if not cartas: return
        
        radio = 3
        for i, tipo in enumerate(cartas):
            angulo = i * (2 * math.pi / len(cartas))
            x = math.cos(angulo) * radio
            z = math.sin(angulo) * radio
            carta = Carta3D(tipo=tipo, posicion=(x, -2, z), scale=(1, 1.4, 0.1))
            self.escena_entidades.append(carta)

    def admin_accion(self, accion):
        valor = self.input_carta.text.strip().upper()
        if accion in ['ins_ini', 'ins_fin', 'buscar', 'elim_esp'] and valor not in CARTAS_INFO:
            self.txt_admin_log.text = f"Error: '{valor}' no es una carta válida."
            return

        try:
            if accion == 'ins_ini':
                self.lista_cartas.insertar_inicio(valor)
                self.txt_admin_log.text = f"Insertado al inicio: {valor}"
            elif accion == 'ins_fin':
                self.lista_cartas.insertar_final(valor)
                self.txt_admin_log.text = f"Insertado al final: {valor}"
            elif accion == 'buscar':
                encontrado = self.lista_cartas.contiene(valor)
                self.txt_admin_log.text = f"¿Contiene {valor}?: {'Sí' if encontrado else 'No'}"
            elif accion == 'elim_ini':
                eliminado = self.lista_cartas.eliminar_inicio()
                self.txt_admin_log.text = f"Eliminado del inicio: {eliminado}"
            elif accion == 'elim_esp':
                exito = self.lista_cartas.eliminar(valor)
                self.txt_admin_log.text = f"Eliminado {valor}: {'Éxito' if exito else 'No encontrado'}"
            
            self.mostrar_lista_circular_mini()
        except Exception as e:
            self.txt_admin_log.text = f"Error: {str(e)}"


# Ejecución de la aplicación
if __name__ == '__main__':
    juego = JuegoCartas()
    juego.app.run()