import pymunk
import pymunk.pygame_util
from typing import List
import pygame
import time
 
  
SHOT_ID_COUNTER = 0

class Ball:
    def __init__(self, team, label, loc):
        self.team = team
        self.label = label
        self.loc = loc

class Table:
    def __init__(self, balls: List[Ball]):
        self.balls = balls # Array of class Ball

class Shot: # only created after ball has been made
    def __init__(self, table: Table, angle, strength, difficulty):
        self.angle = angle
        self.strength = strength
        self.difficulty = difficulty
        self.table = table # initial state (before shot is taken)
        
        global SHOT_ID_COUNTER
        self.shot_id = SHOT_ID_COUNTER
        SHOT_ID_COUNTER += 1

class ShotsTaken:
    def __init__(self, previous_shots: List[Shot]):
        self.previous_shots = previous_shots

class Node:
    def __init__(self, shot: Shot):
        self.parent = None
        self.shot = shot


# Method to create a ball at a location.
# 
# TODO: Mofidy to accept ball object instead of a point.
# TODO: No longer needs to return shape object
def create_ball_at_location(point, space):
    body = pymunk.Body(10, 100)
    body.position = point[0], point[1]
    shape = pymunk.Circle(body, 15)
    # shape.friction = 0
    # shape.ball_object = Ball()
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



# ----------- SHOT EVALUTION -------------------------------------------
#   
#
# CREATE TABLE INITIAL STATE
# PARAMETERS: Ball Locations, array of size 16 (required) of pymunk.Shape
#             Pygame space obejct
# RETURNS:    Nothing
# ASSUMES:    
# def create_initial_state()


# EVALUATE ALL POSSIBLE SHOTS (FOR A GIVEN TABLE STATE)
# PARAMETERS: Table object
#             Pygame space obejct
# RETURNS:    Array of successful shots
# ASSUMES:
# 
# Define search space, angle and strength
# Loop through all search options:(double for loop of possible strength and angle possibilites)
#       Create new state of balls (create_initial_state) (or optionally, create a deep copy and pass to evaluate shot)
#       Call Evaluate shot
#       If shot made:
#           Add to array of successful shots
# Return array of successful shots to search tree algorithm
def evaluate_all_possible_shots(table: Table, space: pygame.Space):
    pass
    
def MOCKED_evaluate_all_possbile_shots(table:Table, space: pygame.Space):
    pass
# EVALUATE SINGLE SHOT
# PARAMETERS: get_shot_diffulty (bool), space, force, angle, array of balls
# ASSUMES:
# RETURNS: shot object (if shot not made, return None)
# ---- BEGIN SIMULATION ----
# Possibly keep track of ball and wall bounces
# If ball made, set shot flag to to true
# ---- END SIMULATION ----
# If shot made flag, create Shot object, return shot object

# GET SHOT DIFFICULTY
# PARAMETERS: 
# ASSUMES:
# REQUIRES:
# ----------- SHOT EVALUTION -------------------------------------------


# -------------- SEARCH TREE -------------------------------------------
# Tree of Shots
# Obtain initial positions of all balls
# Create Table node
#

# -------------- SEARCH TREE ------------------------------------------- 


# step 1
# step 2
# step 3 - evaluate_all_possible_shots(table, space)
# step 4 





# The pool table will have six walls, layout will look like this
#
#   X----0----X----1----X
#   |                   |
#   5                   2
#   |                   |
#   X----4----X----3----X
# Scale is 1:10, cm to pixels
#
# Balls array is always assumed to be of size 16

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

    # TODO: Change to array of Ball objects
    # List contains all pool balls, index 0 is cue ball, other indices correspond to ball numbers
    balls: List[pymunk.Shape] = []
    balls.append(create_ball_at_location((500, 500), space))
    balls.append(create_ball_at_location((200, 500), space))
    balls.append(create_ball_at_location((850, 400), space))
    balls.append(create_ball_at_location((1000, 100), space))
    balls[0].color = (255, 255, 255, 255)


    force_applied = False
    paused = True

    # MODIFY GAME LOOP TO INTERFACE WITH METHODS
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