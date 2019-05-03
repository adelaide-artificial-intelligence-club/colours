# James Keal, 02-MAY-2019

import sys, time, random, pygame
from deap import base, creator, tools

# initialise pygame
pygame.font.init()
font = pygame.font.Font('Roboto-Light.ttf', 32)

# draw a sprite onto the screen
def blit(screen, sprite, pos, angle=0):
    def rotate(image, rect, angle):
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = rot_image.get_rect(center=rect.center)
        return rot_image, rot_rect
    screen.blit(*rotate(sprite, sprite.get_rect(center=pos), angle))

# a colour is a list of 24 binary values with a draw method
class Colour(list):
    def __init__(self, iterable=[], pos=(0,0), size=(100,100), center=False):
        iterable = list(iterable)
        iterable = (24-len(iterable))*[0] + iterable[-24:]
        super().__init__(iterable)
        if center: pos = pos[0] - size[0]/2, pos[1] - size[1]/2
        self.rect = pygame.Rect(*pos, *size)

    def __str__(self):
        return ''.join(str(i) for i in self)

    def __int__(self):
        return int(str(self), 2)

    def rgb(self):
        s = str(self)
        return int(s[0:8], 2), int(s[8:16], 2), int(s[16:24], 2)

    def draw(self, screen):
        pygame.draw.rect(screen, self.rgb(), self.rect)

# a class to hold text with a draw method
class Label(object):
    def __init__(self, text, pos=(0,0), colour=(0,0,0)):
        super().__init__()
        self.pos, self.colour = pos, colour
        self.surface = font.render(text, False, self.colour)

    def draw(self, screen):
        blit(screen, self.surface, self.pos)

# a window and its associated drawable objects
class Panel(object):
    def __init__(self, size):
        super().__init__()
        self.screen = None
        self.size = self.width, self.height = size
        self.bg_colour = 41, 43, 50
        self.objects = []
        self.target = None

    def add(self, object):
        self.objects.append(object)

    def init_screen(self):
        pygame.init()
        self.screen = pygame.display.set_mode(self.size)

    def draw(self, objects=[]):
        if not self.screen:
            self.init_screen()

        step, new, play = False, False, False

        # keyboard controls
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    step = True # step one generation
                if event.key == pygame.K_n:
                    new = True # pick a new target colour
                if event.key == pygame.K_SPACE:
                    play = True # iterate continuously

        self.screen.fill(self.bg_colour)

        for object in objects + self.objects:
            object.draw(self.screen)

        self.target.draw(self.screen)
        pygame.display.update()
        return step, new, play

# entry point
def main(CXPB=0.5, MUTPB=0.2):

    # initialise genetic algorithm
    creator.create('Fitness', base.Fitness, weights=(1.0,))
    creator.create('Individual', list, fitness=creator.Fitness)

    ga = base.Toolbox()

    ga.register('binary', random.randint, 0, 1)
    ga.register('individual', tools.initRepeat, creator.Individual, ga.binary, 24)
    ga.register('population', tools.initRepeat, list, ga.individual)

    # fitness function
    def match(ind, target):
        ind.fitness.values = sum(i == j for i, j in zip(ind, target)),

    ga.register('evaluate', match)
    ga.register('mate', tools.cxTwoPoint)
    ga.register('mutate', tools.mutFlipBit, indpb=0.05)
    ga.register('select', tools.selTournament, tournsize=3)

    # initialise panel
    panel_size = W, H = 1280, 720
    squ_size = w, h = W/8, (H - 20)/5
    panel = Panel(panel_size)
    panel.add(Label('Current goal:', (2*W/5, h/2+10), (224,224,224)))

    # set a new target colour
    def new_target():
        panel.target = Colour(ga.individual(), (3*W/5, h/2+10), squ_size, center=True)

    # randomly generate initial population
    pop, gen = ga.population(n=32), 1
    playing = False
    new_target()

    # genetic algorithm loop
    while True:

        # evaluate all individuals
        for ind in pop:
            if not ind.fitness.valid:
                ga.evaluate(ind, panel.target)

        # draw all individuals and get keyboard inputs
        grid = []
        for n, ind in enumerate(pop):
            i, j = n%8, int(n/8)
            grid.append(Colour(ind, pos=(i*w, (j+1)*h+20), size=squ_size))
        step, new, play = panel.draw(grid)
        if play: playing = False if playing else True
        if new: new_target()

        # step one generation
        if step or playing:
            print('Generation', gen, '...')
            best = tools.selBest(pop, 1)[0]
            print('Best:', hex(int(Colour(best))), '- Fitness:', best.fitness)

            # select
            children = list(map(ga.clone, ga.select(pop, len(pop))))

            # mate
            for child_i, child_j in zip(children[::2], children[1::2]):
                if random.random() < CXPB:
                    ga.mate(child_i, child_j)
                    del child_i.fitness.values, child_j.fitness.values

            # mutate
            for child in children:
                if random.random() < MUTPB:
                    ga.mutate(child)
                    del child.fitness.values

            # update population
            pop, gen = children, gen + 1

            # occasionally pick a new target
            if playing:
                time.sleep(0.1)
                if not gen % 64:
                    new_target()

if __name__ == '__main__':
    main()
