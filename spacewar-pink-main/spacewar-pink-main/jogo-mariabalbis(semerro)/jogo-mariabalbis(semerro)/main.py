from dataclasses import dataclass
import pyxel
import math
import random

#CORES permitidas: 
#COLOR_BLACK
#COLOR_NAVY
#COLOR_PURPLE
#COLOR_GREEN
#COLOR_BROWN
#COLOR_DARK_BLUE
#COLOR_LIGHT_BLUE
#COLOR_WHITE
#COLOR_RED
#COLOR_ORANGE
#COLOR_YELLOW
#COLOR_LIME
#COLOR_CYAN
#COLOR_GRAY
#COLOR_PINK
#COLOR_PEACH

#Classe que define as mercadorias para pontuação
#Devem ser coletadas pelo jogador
@dataclass
class Merch:
    x:int
    y:int
    points:int

    def get_color(self):
        match self.points:
            case 10:
                return pyxel.COLOR_CYAN
            case 20:
                return pyxel.COLOR_LIME
            case 40:
                return pyxel.COLOR_PINK
            case 80:
                return pyxel.COLOR_PEACH
            case -10:
                return pyxel.COLOR_DARK_BLUE
            case -30:
                return pyxel.COLOR_ORANGE
            case -50:
                return pyxel.COLOR_RED
            case _:
                return pyxel.COLOR_WHITE

# Classe para as informações das naves
@dataclass
class Ship:
    x:int
    y:int
    rotation: float = 0 #angulo de rotação (radianos)
    rotation_dir: int = 0 # -1=esquerda, 0=sem rotação, 1=direita
    acceleration: int = 0
    exploded:bool = False
    explosao_timer:int = 0
    points:int = 0
    lives:int = 3
    
##########################
### Definição de constantes para configuração
##########################
#Constantes para configuração do movimento das naves
SHIP_RADIUS = 8
ROTATION_SPEED = 0.03
TOP_SPEED = 10
MAX_ACCELERATION = 2
ACCELERATION_DELTA = 0.02
#Constantes para definição da estrela
STAR_POSITION = { 'x': 150, 'y': 150 }
STAR_SCALE = 3
STAR_RADIUS = 8 * STAR_SCALE
STAR_COLOR = pyxel.COLOR_PINK
#Limites do mapa
MAP_WIDTH = 300
MAP_HEIGHT = 300
#Frames de invulnerabilidade/explosão após uma colisão
INVULNERABILIDADE = 60

#Definições de pontuação para distribuição aleatória
POINTS = [10,20,-10,40,-30,80,-50]
WEIGHTS = [10,11,20,21,40,41,42]
WEIGHT_BUDGET = 1000

#Mercadorias que podem ser coletadas pelo jogador
MERCHS_IN_PLAY = []
#Quantidade máxima de mercadorias no mapa e intervalo (em frames) de reaparecimento
MAX_MERCHS = 40
RESPAWN_INTERVAL = 90

def calcula_distancia_quadrada(x1, y1, x2, y2):
    return (x2 - x1) ** 2 + (y2 - y1) ** 2

#################################
### Funções para o controle da movimentação das naves
#################################
def set_rotation(ship, direction) :
    if ship.rotation_dir == direction :
        return
    if ship.rotation_dir == -direction :
        ship.rotation_dir = 0
    else:
        ship.rotation_dir = direction

def unset_rotation(ship, direction) :
    if ship.rotation_dir == direction :
        ship.rotation_dir = 0
    elif ship.rotation_dir == -direction :
        return
    
def rotate_ship(ship):
    if ship.rotation_dir != 0:
        ship.rotation += ship.rotation_dir*ROTATION_SPEED

def move_ship(ship):
    #Propulsores da nave
    # Vetor que determina a direção de movimento da nave
    direction_vec = { 'x': math.cos(ship.rotation), 'y': math.sin(ship.rotation) }

    dx = STAR_POSITION['x'] - ship.x
    dy = STAR_POSITION['y'] - ship.y

    distancia = calcula_distancia_quadrada(ship.x, ship.y, STAR_POSITION['x'], STAR_POSITION['y'])

    G = 15

    if distancia != 0:
        gravidade_x = (dx/distancia) * G
        gravidade_y = (dy/distancia) * G
    else:
        gravidade_x = 0
        gravidade_y = 0

    ship.x += direction_vec['x'] * ship.acceleration + gravidade_x
    ship.y += direction_vec['y'] * ship.acceleration + gravidade_y

def move_scraps():

    G = 6

    for scrap in MERCHS_IN_PLAY:

        dx = STAR_POSITION['x'] - scrap.x
        dy = STAR_POSITION['y'] - scrap.y

        distancia = calcula_distancia_quadrada(scrap.x, scrap.y, STAR_POSITION['x'], STAR_POSITION['y'])

        if distancia != 0:
            scrap.x += (dx/distancia) * G
            scrap.y += (dy/distancia) * G
            
def set_acceleration(ship, magnitude):
    ship.acceleration += magnitude * ACCELERATION_DELTA
    if ship.acceleration > MAX_ACCELERATION :
        ship.acceleration = MAX_ACCELERATION
    elif (ship.acceleration < 0):
        ship.acceleration = 0

#####################
#### Funções de inicialização das Mercadorias (pontos)
#####################
# Seleção aleatória com base em pesos
def select_points():
    total = 0
    for w in WEIGHTS:
        total += w
    # Número aleatório [1, total]
    rd = random.randint(1,total)
    cursor = 0
    for i in range(len(WEIGHTS)):
        cursor += WEIGHTS[i]
        if (cursor >= rd):
            return (POINTS[i],WEIGHTS[i])
    return (POINTS[-1],WEIGHTS[-1])

def cria_mercadoria():
    p,w = select_points()
    scrap = Merch(random.randint(0,MAP_WIDTH),random.randint(0,MAP_HEIGHT),p)
    return scrap, w

def spawn_scrap():
   budget = WEIGHT_BUDGET
   while budget > 0:
       scrap,w = cria_mercadoria()
       MERCHS_IN_PLAY.append(scrap)
       budget -= w

def respawn_scrap():
    if len(MERCHS_IN_PLAY) < MAX_MERCHS and pyxel.frame_count % RESPAWN_INTERVAL == 0:
        scrap,_ = cria_mercadoria()
        MERCHS_IN_PLAY.append(scrap)

###########################
#### Funções para verificação de colisões
###########################

#Verifica colisões das mercadorias
#RETORNA: Lista de Merchs pegos pela nave, lista de Merchs engolidos pela estrela
def check_scrap_collision(ship):
    remover = []

    for scrap in MERCHS_IN_PLAY:
        distancia = calcula_distancia_quadrada(ship.x, ship.y, scrap.x, scrap.y)

        if distancia <= SHIP_RADIUS ** 2:
            ship.points += scrap.points
            remover.append(scrap)

    for scrap in remover:
        MERCHS_IN_PLAY.remove(scrap)

    remover2 = []

    for scrap in MERCHS_IN_PLAY:
        distancia = calcula_distancia_quadrada(scrap.x, scrap.y, STAR_POSITION['x'], STAR_POSITION['y'])

        if distancia <= STAR_RADIUS ** 2:
            remover2.append(scrap)

    for scrap in remover2:
        MERCHS_IN_PLAY.remove(scrap)

    return remover, remover2

def atinge_nave(ship):
    ship.lives -= 1
    ship.x = 50
    ship.y = 50
    ship.acceleration = 0
    ship.exploded = True
    ship.explosao_timer = INVULNERABILIDADE

# Atualiza o estado de explosão/invulnerabilidade da nave
def atualiza_explosao(ship):
    if ship.exploded:
        ship.explosao_timer -= 1
        if ship.explosao_timer <= 0:
            ship.exploded = False

# Verifica colisões da nave
def check_collisions(ship):
    if ship.exploded:
        return

    distancia = calcula_distancia_quadrada(ship.x, ship.y, STAR_POSITION['x'], STAR_POSITION['y'])

    if distancia <= (STAR_RADIUS + SHIP_RADIUS) ** 2:
        atinge_nave(ship)
        return

    if ship.x < 0 or ship.x > MAP_WIDTH or ship.y < 0 or ship.y > MAP_HEIGHT:
        atinge_nave(ship)

# Desenha um coração simples (duas bolinhas em cima + um triângulo embaixo)
def draw_heart(x, y, color):
    pyxel.circ(x + 2, y + 2, 2, color)
    pyxel.circ(x + 6, y + 2, 2, color)
    pyxel.tri(x, y + 3, x + 8, y + 3, x + 4, y + 8, color)

# Desenha um coração para cada vida restante do jogador
def draw_lives(x, y, lives):
    for i in range(lives):
        draw_heart(x + i * 10, y, pyxel.COLOR_RED)

# Desenha a legenda explicando quantos pontos cada cor de mercadoria vale.
# Reaproveita o Merch.get_color() para garantir que a cor mostrada aqui
# seja sempre a mesma usada de verdade no jogo.
def draw_legend(x, y):
    pyxel.text(x, y, "PONTOS", pyxel.COLOR_WHITE)
    for i, pontos in enumerate(sorted(POINTS, reverse=True)):
        linha_y = y + 8 + i * 8
        cor = Merch(0, 0, pontos).get_color()
        pyxel.circ(x + 2, linha_y + 2, 2, cor)
        texto = f"+{pontos}" if pontos > 0 else str(pontos)
        pyxel.text(x + 8, linha_y, texto, pyxel.COLOR_WHITE)

######################
### Classe principal da game engine
######################
class App:
    c_needle = Ship(50,50)

    def __init__(self):
        pyxel.init(MAP_WIDTH, MAP_HEIGHT)
        pyxel.load("my_resource.pyxres")
        self.x = 0
        spawn_scrap()
        pyxel.run(self.update, self.draw)

    def reinicia(self):
        self.c_needle = Ship(50,50)
        MERCHS_IN_PLAY.clear()
        spawn_scrap()
        
    # Processa a entrada de teclado do usuário
    def processa_teclado(self):
        if pyxel.btn(pyxel.KEY_W):
            set_acceleration(self.c_needle, 1)
        elif pyxel.btn(pyxel.KEY_S):
            set_acceleration(self.c_needle, -1)
        if pyxel.btn(pyxel.KEY_A):
            set_rotation(self.c_needle, -1)
        elif pyxel.btn(pyxel.KEY_D):
            set_rotation(self.c_needle, 1)

        if not pyxel.btn(pyxel.KEY_A):
            unset_rotation(self.c_needle, -1)
        if not pyxel.btn(pyxel.KEY_D):
            unset_rotation(self.c_needle, 1)

    #Atualiza as informações do jogo ANTES de desenhar cada frame
    # 1. Verifica se há alguma tecla pressionada
    # 2. Aplica rotação na Nave
    # 3. Aplica o movimento da nave
    def update(self):
        if self.c_needle.lives <= 0:
            if pyxel.btnp(pyxel.KEY_R):
                self.reinicia()
            return
        self.processa_teclado()
        rotate_ship(self.c_needle)
        move_ship(self.c_needle)
        move_scraps()
        respawn_scrap()
        atualiza_explosao(self.c_needle)
        check_collisions(self.c_needle)
        check_scrap_collision(self.c_needle)

    #Faz o desenho da tela do jogo
    def draw(self):
        if self.c_needle.lives <= 0:
            pyxel.cls(0)
            pyxel.text(100, 150, "GAME OVER", pyxel.COLOR_RED)
            pyxel.text(100, 160, f"Pontos: {self.c_needle.points}", pyxel.COLOR_WHITE)
            pyxel.text(100, 170, "Aperte R para reiniciar", pyxel.COLOR_WHITE)
            return
        pyxel.cls(0)
        needle = self.c_needle
        # Estrela no centro da tela
        pyxel.circ(STAR_POSITION['x'], STAR_POSITION['y'], STAR_RADIUS, STAR_COLOR)
        # Nave do Jogador 1 (Needle) - pisca enquanto está invulnerável
        if not needle.exploded or pyxel.frame_count % 4 < 2:
            pyxel.blt(needle.x, needle.y, 0, 8, 8, 16, 16, rotate=math.degrees(needle.rotation)+90, colkey=0)
        if needle.exploded:
            raio = 4 + (INVULNERABILIDADE - needle.explosao_timer) // 4
            pyxel.circb(needle.x + 8, needle.y + 8, raio, pyxel.COLOR_ORANGE)
        for scrap in MERCHS_IN_PLAY:
            pyxel.circ(scrap.x, scrap.y, 2, col=scrap.get_color())
        draw_lives(10, 5, needle.lives)
        pyxel.text(10, 16, f"Pontos: {needle.points}", pyxel.COLOR_WHITE)
        draw_legend(250, 5)
    
App()
