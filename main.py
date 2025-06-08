import pygame
import pickle
import os
import neat
import random


pygame.init()

WINDOWSIZE = (600, 800)
FLOORPOSITION = 730

display = pygame.display.set_mode(WINDOWSIZE)

BIRDIMAGES = [
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("sprites", "bird1.png")).convert_alpha()
    ),
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("sprites", "bird2.png")).convert_alpha()
    ),
    pygame.transform.scale2x(
        pygame.image.load(os.path.join("sprites", "bird3.png")).convert_alpha()
    ),
]

PIPEIMAGE = pygame.transform.scale2x(
    pygame.image.load(os.path.join("sprites", "pipe.png")).convert_alpha()
)

PIPETOP = pygame.transform.flip(PIPEIMAGE, False, True)

BACKGROUNDIMAGE = pygame.transform.scale(
    pygame.image.load(os.path.join("sprites", "background.png")).convert_alpha(),
    WINDOWSIZE,
)

BASEIMAGE = pygame.transform.scale2x(
    pygame.image.load(os.path.join("sprites", "base.png")).convert_alpha()
)

FONT = pygame.font.SysFont("comicsans", 40)

pygame.display.set_caption("Flappy Bird (AI)")
pygame.display.set_icon(BIRDIMAGES[0])

generation = 0


class Bird:
    """for creating birds"""

    MAXROTATION = 25
    ROTATIONVELOCITY = 20
    ANIMATIONTIME = 5

    def __init__(self, x: int, y: int) -> None:
        """initialize the object

        Args:
            x (int): starting x position
            y (int): starting y position
        """
        self.acceleration = 3
        self.tickCount = 0
        self.velocity = 0
        self.x = x
        self.y = y
        self.tilt = 0
        self.height = self.y
        self.birdImgCount = 0
        self.birdImage = BIRDIMAGES[0]

    def jump(self) -> None:
        """make the bird jump"""
        self.velocity = -10.5
        self.tickCount = 0
        self.height = self.y

    def move(self) -> None:
        """make the bird move"""
        self.tickCount += 1

        displacement = self.velocity * self.tickCount + 0.5 * (
            self.acceleration * self.tickCount**2
        )

        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        self.y += displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAXROTATION:
                self.tilt = self.MAXROTATION

        elif self.tilt > -90:
            self.tilt -= self.ROTATIONVELOCITY

    def draw(self) -> None:
        """draw the bird on pygame window"""
        self.birdImgCount += 1

        if self.birdImgCount <= self.ANIMATIONTIME:
            self.birdImage = BIRDIMAGES[0]

        elif self.birdImgCount <= self.ANIMATIONTIME * 2:
            self.birdImage = BIRDIMAGES[1]

        elif self.birdImgCount <= self.ANIMATIONTIME * 3:
            self.birdImage = BIRDIMAGES[2]

        elif self.birdImgCount <= self.ANIMATIONTIME * 4:
            self.birdImage = BIRDIMAGES[1]

        elif self.birdImgCount <= self.ANIMATIONTIME * 4 + 1:
            self.birdImage = BIRDIMAGES[0]
            self.birdImgCount = 0

        if self.tilt <= -80:
            self.birdImage = BIRDIMAGES[1]
            self.birdImgCount = self.ANIMATIONTIME * 2

        rotatedBirdImg = pygame.transform.rotate(self.birdImage, self.tilt)
        rotatedBirdImgRect = rotatedBirdImg.get_rect(
            center=self.birdImage.get_rect(topleft=(self.x, self.y)).center
        )

        display.blit(rotatedBirdImg, rotatedBirdImgRect.topleft)

    def mask(self) -> pygame.mask.MaskType:
        """creates mask for the current image of bird

        Returns:
            pygame.mask.MaskType: Mask
        """
        return pygame.mask.from_surface(self.birdImage)


class Pipe:
    """represents a pipe object"""

    GAP = 200
    VELOCITY = 5

    def __init__(self, x: int) -> None:
        """initialise pipe object

        Args:
            x (int): position for placing pipe
        """
        self.x = x
        self.height = random.randrange(50, 450)

        self.bottom = self.height + self.GAP
        self.top = self.height - PIPETOP.get_height()
        self.passed = False

    def move(self) -> None:
        """move pipe based on velocity"""
        self.x -= self.VELOCITY

    def draw(self) -> None:
        """draws both top and bottom of the pipe"""
        display.blit(PIPETOP, (self.x, self.top))
        display.blit(PIPEIMAGE, (self.x, self.bottom))

    def collide(self, bird: Bird) -> bool:
        """checks if bird is colliding with the pipe

        Args:
            bird (Bird): bird object

        Returns:
            bool: bird hit the pipe or not
        """
        birdMask = bird.mask()

        pipeTBottomMask = pygame.mask.from_surface(PIPEIMAGE)
        pipeTopMask = pygame.mask.from_surface(PIPETOP)

        pipeTopOffset = (self.x - bird.x, self.top - round(bird.y))
        pipeBottomOffset = (self.x - bird.x, self.bottom - round(bird.y))

        topPipeCollision = birdMask.overlap(pipeTopMask, pipeTopOffset)
        bottomPipeCollision = birdMask.overlap(pipeTBottomMask, pipeBottomOffset)

        return bool(topPipeCollision or bottomPipeCollision)


class Base:
    """represents moving floor of game"""

    VELOCITY = 5
    WIDTH = BASEIMAGE.get_width()

    def __init__(self, y: int) -> None:
        """initialise the base

        Args:
            y (int): position of base
        """
        self.y = y
        self.x2 = self.WIDTH
        self.x1 = 0

    def move(self) -> None:
        """move floor so it looks like its scrolling"""
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self) -> None:
        """draw the floor"""
        display.blit(BASEIMAGE, (self.x1, self.y))
        display.blit(BASEIMAGE, (self.x2, self.y))


def drawSprites(
    birds: list[Bird],
    pipes: list[Pipe],
    base: Base,
    score: int,
    generation: int,
    pipeToUse: Pipe = None,
    drawLines: bool = False,
) -> None:
    """draw sprites on pygame window

    Args:
        birds (list[Bird]): list of birds
        pipes (list[Pipe]): list of pipes
        base (Base): base object
        score (int): score of game
        generation (int): number of current generation
    """
    display.blit(BACKGROUNDIMAGE, (0, 0))

    for pipe in pipes:
        pipe.draw()

    base.draw()

    for bird in birds:
        if drawLines:
            pygame.draw.line(
                display,
                (255, 0, 0),
                (
                    bird.x + bird.birdImage.get_width() // 2,
                    bird.y + bird.birdImage.get_height() // 2,
                ),
                (pipeToUse.x + PIPEIMAGE.get_width() // 2, pipeToUse.bottom),
                3,
            )
            pygame.draw.line(
                display,
                (255, 0, 0),
                (
                    bird.x + bird.birdImage.get_width() // 2,
                    bird.y + bird.birdImage.get_height() // 2,
                ),
                (
                    pipeToUse.x + PIPEIMAGE.get_width() // 2,
                    pipeToUse.bottom - pipeToUse.GAP,
                ),
                3,
            )

        bird.draw()

    scoreText = FONT.render(f"Score: {score}", False, (255, 255, 255))
    generationText = FONT.render(f"Gens: {generation}", False, (255, 255, 255))
    aliveText = FONT.render(f"Alive: {len(birds)}", False, (255, 255, 255))

    display.blit(generationText, (10, 10))
    display.blit(scoreText, (WINDOWSIZE[0] - scoreText.get_width() - 15, 10))
    display.blit(aliveText, (10, 60))

    pygame.display.update()


def main(genomes, config):
    global generation

    neuralnetworks = []
    birds: list[Bird] = []
    genomesList = []

    generation += 1

    for _, genome in genomes:
        genome.fitness = 0
        neuralnetworks.append(neat.nn.FeedForwardNetwork.create(genome, config))

        birds.append(Bird(230, 350))
        genomesList.append(genome)

    base = Base(FLOORPOSITION)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    while True and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        pipeToUse = sorted(
            filter(lambda p: p.x + PIPETOP.get_width() > birds[0].x, pipes),
            key=lambda p: p.x,
        )[0]

        for index, bird in enumerate(birds):
            genomesList[index].fitness += 0.1
            bird.move()

            output = neuralnetworks[index].activate(
                (
                    bird.y,
                    abs(bird.y - pipeToUse.height),
                    abs(bird.y - pipeToUse.bottom),
                ),
            )

            if output[0] > 0.5:
                bird.jump()

        base.move()

        addPipe = False

        for pipe in pipes:
            pipe.move()

            for index, bird in enumerate(birds):
                if pipe.collide(bird):
                    genomesList[index].fitness -= 1
                    neuralnetworks.pop(index)
                    genomesList.pop(index)
                    birds.pop(index)

            if pipe.x + PIPETOP.get_width() < 0:
                pipes.remove(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                addPipe = True

        if addPipe:
            score += 1

            for genome in genomesList:
                genome.fitness += 5

            pipes.append(Pipe(WINDOWSIZE[0]))

        for index, bird in enumerate(birds):
            if (
                bird.y + bird.birdImage.get_height() - 10 >= FLOORPOSITION
                or bird.y < -50
            ):
                neuralnetworks.pop(index)
                genomesList.pop(index)
                birds.pop(index)

        drawSprites(birds, pipes, base, score, generation)

        if score > 20:
            with open(r"model\model.pickle", "wb") as file:
                pickle.dump(
                    sorted(genomesList, key=lambda genome: genome.fitness)[0], file
                )
                # break


configPath = os.path.join(os.path.dirname(__file__), "config.txt")
config = neat.config.Config(
    neat.DefaultGenome,
    neat.DefaultReproduction,
    neat.DefaultSpeciesSet,
    neat.DefaultStagnation,
    configPath,
)

population = neat.Population(config)

population.add_reporter(neat.StdOutReporter(True))
population.add_reporter(neat.StatisticsReporter())

winner = population.run(main, 50)
print("Best genome:\n:{!s}".format(winner))
