import random
import pygame
from game.maze import generate_maze, CELL
from game.entities import Player, Enemy

COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 50
FPS = 60

# Difficulty ramp
BASE_INTERVAL = 20      # starting enemy move_interval (frames between moves)
RAMP_EVERY_MS = 15000   # speed up every 15 seconds
RAMP_STEP = 2           # reduce move_interval by this much each tier
MIN_INTERVAL = 5        # enemies never move faster than this
PELLET_RADIUS = 9

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        self.hud_font = pygame.font.SysFont("monospace", 16)
        self.exit_font = pygame.font.SysFont("monospace", 12, bold=True)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        # One enemy in each corner the player doesn't start in
        self.enemies = [
            Enemy(ROWS-1, COLS-1),   # bottom-right (original)
            Enemy(0, COLS-1),        # top-right
            Enemy(ROWS-1, 0),        # bottom-left
        ]
        self.exit_rect = pygame.Rect((COLS//2)*CELL+5, (ROWS//2)*CELL+5, CELL-10, CELL-10)
        self.caught = False
        self.won = False
        self.start_ticks = pygame.time.get_ticks()
        self.speed_tier = 0
        # Power pellet: random cell, avoiding start, exit and enemy corners
        excluded = {(0, 0), (ROWS//2, COLS//2), (ROWS-1, COLS-1), (0, COLS-1), (ROWS-1, 0)}
        cells = [(r, c) for r in range(ROWS) for c in range(COLS) if (r, c) not in excluded]
        pr, pc = random.choice(cells)
        self.pellet_rect = pygame.Rect(0, 0, PELLET_RADIUS*2, PELLET_RADIUS*2)
        self.pellet_rect.center = (pc*CELL + CELL//2, pr*CELL + CELL//2)
        self.pellet_active = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    def update(self):
        if self.caught or self.won: return

        # Difficulty ramp: one tier per RAMP_EVERY_MS of play time
        elapsed = pygame.time.get_ticks() - self.start_ticks
        self.speed_tier = elapsed // RAMP_EVERY_MS
        interval = max(MIN_INTERVAL, BASE_INTERVAL - RAMP_STEP * self.speed_tier)

        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)
        if self.pellet_active and self.player.rect.colliderect(self.pellet_rect):
            self.pellet_active = False
            for enemy in self.enemies:
                enemy.freeze()
        for enemy in self.enemies:
            enemy.move_interval = interval
            enemy.update(self.walls, self.player, ROWS, COLS)
            if self.player.rect.colliderect(enemy.rect):
                self.caught = True
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True

    def draw(self):
        self.screen.fill((230, 220, 210))
        wc=(50,40,60)
        for r in range(ROWS):
            for c in range(COLS):
                x,y=c*CELL,r*CELL
                w=self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen,wc,(x,y),(x+CELL,y),3)
                if w[1]: pygame.draw.line(self.screen,wc,(x,y+CELL),(x+CELL,y+CELL),3)
                if w[2]: pygame.draw.line(self.screen,wc,(x+CELL,y),(x+CELL,y+CELL),3)
                if w[3]: pygame.draw.line(self.screen,wc,(x,y),(x,y+CELL),3)
        pygame.draw.rect(self.screen,(80,200,80),self.exit_rect,border_radius=4)
        lbl=self.exit_font.render("EXIT",True,(20,80,20))
        self.screen.blit(lbl,lbl.get_rect(center=self.exit_rect.center))
        if self.pellet_active:
            pygame.draw.circle(self.screen, (255, 215, 0), self.pellet_rect.center, PELLET_RADIUS)
            pygame.draw.circle(self.screen, (200, 150, 0), self.pellet_rect.center, PELLET_RADIUS, 2)
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        hud=pygame.Rect(0,ROWS*CELL,WIDTH,50)
        pygame.draw.rect(self.screen,(30,30,50),hud)
        info=self.hud_font.render("Reach the EXIT!  R=Restart",True,(200,200,200))
        self.screen.blit(info,info.get_rect(midleft=(8,ROWS*CELL+25)))
        interval = max(MIN_INTERVAL, BASE_INTERVAL - RAMP_STEP * self.speed_tier)
        tier_text = "Speed: MAX" if interval == MIN_INTERVAL else f"Speed: {self.speed_tier + 1}"
        tier = self.hud_font.render(tier_text, True, (255, 200, 80))
        self.screen.blit(tier, tier.get_rect(midright=(WIDTH-8, ROWS*CELL+25)))
        if self.caught:
            self._overlay("CAUGHT!", (220,60,60))
        if self.won:
            self._overlay("ESCAPED!", (80,220,80))
        pygame.display.flip()

    def _overlay(self, text, color):
        surf=pygame.Surface((WIDTH,ROWS*CELL),pygame.SRCALPHA)
        surf.fill((0,0,0,140))
        self.screen.blit(surf,(0,0))
        msg=self.big_font.render(text,True,color)
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(msg,(WIDTH//2-msg.get_width()//2,ROWS*CELL//2-30))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,ROWS*CELL//2+20))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
