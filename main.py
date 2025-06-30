import random
import pygame

from simon_highscore import load_scores, save_scores

# ----------------- Config -----------------
WIDTH, HEIGHT = 540, 640
FPS = 60
GRID_SIZE = 3
HEADER_HEIGHT = 140  # bigger top bar to fit all texts
TILE_SIZE = (HEIGHT - HEADER_HEIGHT) // GRID_SIZE
MARGIN_TOP = HEADER_HEIGHT
GRID_PIXEL = TILE_SIZE * GRID_SIZE
MARGIN_LEFT = (WIDTH - GRID_PIXEL) // 2

# Base colors for each tile (3x3)
ROW_COLORS = [
    [(200, 0, 0), (0, 180, 0), (0, 0, 200)],  # R, G, B
    [(220, 120, 0), (120, 0, 180), (0, 180, 180)],  # orange, purple, cyan
    [(220, 220, 0), (200, 0, 120), (0, 120, 120)],  # yellow, pink-ish, teal
]

HIGHLIGHT_FACTOR = 1.4  # multiply to lighten when flashing
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ----------------- Helpers -----------------

def lighten(color, factor):
    return tuple(min(int(c * factor), 255) for c in color)


# ----------------- Tile -----------------

class Tile:
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.rect = pygame.Rect(MARGIN_LEFT + col * TILE_SIZE, MARGIN_TOP + row * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def draw(self, surface, highlight=False):
        c = lighten(self.color, HIGHLIGHT_FACTOR) if highlight else self.color
        pygame.draw.rect(surface, c, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 1)


# ----------------- Simon Game -----------------

class SimonGame:
    STATE_SHOW = "show"
    STATE_PLAYER = "player"
    STATE_GAMEOVER = "gameover"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simon Says – Color Memory")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)

        # Build tiles grid
        self.tiles = [
            [Tile(r, c, ROW_COLORS[r][c]) for c in range(GRID_SIZE)]
            for r in range(GRID_SIZE)
        ]

        # Game vars
        self.sequence = []
        self.player_index = 0
        self.state = None
        self.score = 0
        self.highscores = load_scores()

        self.start_new_game()

    # ------------- Game flow -------------

    def start_new_game(self):
        self.sequence = [self.random_tile_index()]
        self.player_index = 0
        self.score = 0
        self.state = SimonGame.STATE_SHOW
        print(f"Nueva partida -> secuencia inicial {self.sequence}")

    def random_tile_index(self):
        return random.randint(0, GRID_SIZE * GRID_SIZE - 1)

    def extend_sequence(self):
        # Ensure no tile appears more than 2 times in the overall sequence
        while True:
            idx = self.random_tile_index()
            if self.sequence.count(idx) < 2:
                self.sequence.append(idx)
                break
        print(f"Secuencia extendida: {self.sequence}")

    # ------------- Drawing -------------

    def draw_board(self, highlight_index=None):
        for idx, tile in enumerate(self.all_tiles_flat()):
            tile.draw(self.screen, highlight=(idx == highlight_index))

    def all_tiles_flat(self):
        return [tile for row in self.tiles for tile in row]

    def draw_ui(self):
        score_surf = self.font.render(f"Puntaje: {self.score}", True, BLACK)
        # Draw score top-left
        self.screen.blit(score_surf, (10, 10))

        if self.state == SimonGame.STATE_GAMEOVER:
            over_surf = self.font.render("¡Perdiste! (Espacio para reiniciar)", True, BLACK)
            rect = over_surf.get_rect(center=(WIDTH // 2, 40))
            self.screen.blit(over_surf, rect)
            y = 70
            hs_title = self.font.render("Mejores 3 puntajes:", True, BLACK)
            self.screen.blit(hs_title, (10, y))
            y += 30
            for i, s in enumerate(self.highscores, 1):
                hs = self.font.render(f"{i}. {s}", True, BLACK)
                self.screen.blit(hs, (30, y))
                y += 25
        elif self.state == SimonGame.STATE_SHOW:
            info = self.font.render("Observa la secuencia...", True, BLACK)
            rect = info.get_rect(center=(WIDTH // 2, 40))
            self.screen.blit(info, rect)
        elif self.state == SimonGame.STATE_PLAYER:
            info = self.font.render("Tu turno", True, BLACK)
            rect = info.get_rect(center=(WIDTH // 2, 40))
            self.screen.blit(info, rect)

    # ------------- Sequence display -------------

    def show_sequence(self):
        # Brief pause before flashing sequence
        self.screen.fill(WHITE)
        self.draw_board()
        self.draw_ui()
        pygame.display.flip()
        pygame.time.delay(400)

        for idx in self.sequence:
            # Highlight tile
            self.screen.fill(WHITE)
            self.draw_board(highlight_index=idx)
            self.draw_ui()
            pygame.display.flip()
            pygame.time.delay(600)

            # Pause with normal board
            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_ui()
            pygame.display.flip()
            pygame.time.delay(400)

        self.state = SimonGame.STATE_PLAYER
        self.player_index = 0

    # ------------- Event handling -------------

    def handle_click(self, pos):
        for idx, tile in enumerate(self.all_tiles_flat()):
            if tile.rect.collidepoint(pos):
                self.draw_board(highlight_index=idx)
                self.draw_ui()
                pygame.display.flip()
                pygame.time.delay(150)
                correct = idx == self.sequence[self.player_index]
                if correct:
                    self.player_index += 1
                    if self.player_index == len(self.sequence):
                        # Round complete
                        self.score += 1
                        self.extend_sequence()
                        self.state = SimonGame.STATE_SHOW
                else:
                    # Game over
                    self.state = SimonGame.STATE_GAMEOVER
                    self.highscores = save_scores(self.highscores + [self.score])
                break

    # ------------- Main loop -------------

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == SimonGame.STATE_PLAYER:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN and self.state == SimonGame.STATE_GAMEOVER:
                    if event.key == pygame.K_SPACE:
                        self.start_new_game()

            if self.state == SimonGame.STATE_SHOW:
                self.show_sequence()

            # Draw frame
            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_ui()
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    SimonGame().run() 