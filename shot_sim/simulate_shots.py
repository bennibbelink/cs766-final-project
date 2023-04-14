import pymunk
import pymunk.pygame_util
from typing import List
import pygame
import time


# Method to create a ball at a location.
# 
def create_ball_at_location(point, space):
    body = pymunk.Body(10, 100)
    body.position = point[0], point[1]
    shape = pymunk.Circle(body, 15)
    shape.friction = 0
    shape.collision_type = 2
    shape.elasticity = 1
    shape.body = body
    space.add(body, shape)
    pivot = pymunk.PivotJoint(space.static_body, body, (0, 0), (0, 0))
    space.add(pivot)
    pivot.max_bias = 0
    pivot.max_force = 1000
    return shape


# Method to create the walls inside the space. Eiter 2 points can be provided, which will be assumed
# to siginify the two inside boundaries, or 4 points will be provided to define a quadrilateral of 
# the wall,
def create_wall(points, space):
    if len(points) == 2:
        raise NotImplementedError
    elif len(points) == 4:
        shape = pymunk.Poly(space.static_body, [(points[0][0], points[0][1]), (points[1][0], points[1][1]), (points[2][0], points[2][1]), (points[3][0], points[3][1])])
        shape.elasticity = 1
        shape.color = (255, 255, 255, 255)
        space.add(shape)
        return shape
    else:
        raise ValueError


# Create triggers that balls collide with that will delete them
def create_pockets(walls, space):
    pass



# The pool table will have six walls, layout will look like this
#
#   X----0----X----1----X
#   |                   |
#   5                   2
#   |                   |
#   X----4----X----3----X
# Scale is 1:10, cm to pixels

def main():
    pygame.init()
    screen = pygame.display.set_mode((1300, 800))
    clock = pygame.time.Clock()
    running = True

    space = pymunk.Space()
    space.gravity = 0, 0
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    
    # WALLS ARE ASSUMED TO BE CREATED IN A CERTAIN ORDER, FOR POCKET GENERATION
    walls: List[pymunk.Shape] = []
    walls.append(create_wall([(100, 50), (600, 50), (602, 40), (90, 40)], space))
    walls.append(create_wall([(650, 50), (1150, 50), (1160, 40), (648, 40)], space))
    walls.append(create_wall([(60, 90), (60, 590), (50, 600), (50, 80)], space))
    walls.append(create_wall([(1190, 90), (1190, 590), (1200, 600), (1200, 80)], space))
    walls.append(create_wall([(100, 630), (600, 630), (602, 640), (90, 640)], space))
    walls.append(create_wall([(650, 630), (1150, 630), (1160, 640), (648, 640)], space))

    # Triggers for detecting balls entering pockets
    # pockets: List[pymunk.Shape] =[]
    # pockets.append()

    # List contains all pool balls, index 0 is cue ball, other indices correspond to ball numbers
    balls: List[pymunk.Shape] = []
    balls.append(create_ball_at_location((500, 500), space))
    balls.append(create_ball_at_location((200, 500), space))
    balls.append(create_ball_at_location((850, 400), space))
    balls.append(create_ball_at_location((1000, 100), space))
    balls[0].color = (255, 255, 255, 255)


    force_applied = False
    paused = True
    while running:

        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                paused = not paused

        if not paused:
            if not force_applied:
                balls[0].body.apply_impulse_at_local_point((4000, -3350), (0, 0)) # This is a single force being applied
                force_applied = True

            for ball in balls:
                # TODO: Switch to actual
                if ball.body.position[0] > 1200:
                    print("REMOVING")
                    space.remove(ball, ball.body)
                    balls.remove(ball)

            screen.fill(pygame.Color("black"))
            space.debug_draw(draw_options)
            pygame.display.flip()
            fps = 60
            dt = 1.0 / fps
            space.step(dt) # These can be modified to sped up the time scale
            clock.tick(fps)


if __name__ == "__main__":
    main()