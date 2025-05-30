import pygame
import neat  # using neat for reinforcement
import time
import os
import random

pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800
GEN = 0
BIRDS_IMG = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bird3.png"))),
]
PIPE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join("assets", "pipe.png"))
)
BASE_IMG = pygame.transform.scale2x(
    pygame.image.load(os.path.join("assets", "base.png"))
)
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("assets", "bg.png")))
STAT_FONT = pygame.font.SysFont("comicsans", 30)
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird AI")


class Bird:
    IMGS = BIRDS_IMG
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        displacement = self.vel * (self.tick_count) + 0.5 * (3) * (self.tick_count) ** 2
        if displacement >= 16:
            displacement = (displacement / abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center
        )

        win.blit(rotated_img, new_rect.topleft)

    def mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(30, 470)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_collide = bird_mask.overlap(bottom_mask, bottom_offset)
        t_collide = bird_mask.overlap(top_mask, top_offset)

        if b_collide or t_collide:
            return True

        return False


class Base:
    VEL = 5  # same as pipe
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score, gen, live):
    win.blit(BG_IMG, (0, 0))
    for bird in birds:
        bird.draw(win)
    base.draw(win)

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render(f"Score: {score}", True, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 20 - text.get_width(), 10))

    text = STAT_FONT.render(f"Gen: {gen}", True, (255, 255, 255))
    win.blit(text, (20, 10))

    text = STAT_FONT.render(f"Live: {live}", True, (255, 255, 255))
    win.blit(text, (20, 50))

    pygame.display.update()


def eval_genomes(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    for _, g in genomes:  # tuple(id, genome)
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    score = 0
    pipes = [Pipe(600)]

    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if (
                len(pipes) > 1
                and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width()
            ):
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1
            output = nets[x].activate(
                (
                    bird.y,
                    abs(bird.y - pipes[pipe_ind].height),
                    abs(bird.y - pipes[pipe_ind].bottom),
                )
            )

            if output[0] > 0.5:
                bird.jump()

        # bird.move()
        rem = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # bird that didnt hit had a higher fitness level and was preferred in nn
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                # all genome will have +5
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN, len(birds))


def run(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )
    p = neat.Population(config)
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(eval_genomes, 50)
    print("\nBest genome:\n{!s}".format(winner))


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config = os.path.join(local_dir, "config-feedforward.txt")
    run(config)
