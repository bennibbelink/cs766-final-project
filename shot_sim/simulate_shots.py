import pymunk
import pymunk.pygame_util
from typing import List
import pygame
import math
import queue
 

SHOT_ID_COUNTER = 0
SOLIDS_TEAM_ID= 0
STRIPES_TEAM_ID = 1
CUE_BALL_ID = 2
POCKET_ID = 3
WALL_ID = 4
EIGHT_BALL_ID = 5


best_running_difficulty = -1
DRAW = False

class MyPoly(pymunk.Poly):
    def __init__(self):
        super.__init__()
        self.id = None
    
class Ball:
    def __init__(self, team, label, loc):
        self.team = team
        self.label = label
        self.loc = loc

class Table:
    def __init__(self, balls: List[Ball]):
        self.balls = balls # Array of class Ball
        self.game_won = False

class Shot: # only created after ball has been made
    def __init__(self, table: Table, angle, strength, difficulty):
        self.angle = angle
        self.strength = strength
        self.difficulty = difficulty
        self.table = table # initial state (before shot is taken)

        global SHOT_ID_COUNTER
        self.shot_id = SHOT_ID_COUNTER
        SHOT_ID_COUNTER += 1

class Node:
    def __init__(self, shot: Shot):
        self.parent = None
        self.shot = shot
        self.running_difficulty = 0

    def set_running_difficulty(self, diff):
        self.running_difficulty = diff


def simulate_shot(shot: Shot):
    
# Method to create a ball at a location.
def create_ball_at_location(point, space, id):
    body = pymunk.Body(10, 100)
    body.position = point[0], point[1]
    shape = pymunk.Circle(body, 15)
    shape.id = id
    if id == 0:
        shape.collision_type = CUE_BALL_ID
        shape.color = (255, 255, 255, 255)
    elif id <= 7:
        shape.collision_type = SOLIDS_TEAM_ID
        shape.color = (255, 0, 255, 255)
    elif id == 8:
        shape.collision_type = EIGHT_BALL_ID
    else:
        shape.collision_type = STRIPES_TEAM_ID
        shape.color = (255, 255, 0, 255)
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
def create_pocket(top_left_corner: tuple, length, space):
    shape = pymunk.Poly(space.static_body, [top_left_corner,
        (top_left_corner[0], top_left_corner[1] + length),
        (top_left_corner[0] + length, top_left_corner[1] + length), 
        (top_left_corner[0] + length, top_left_corner[1])])
    
    # DEBUG
    shape.color = (255, 0, 0, 255)

    shape.collision_type = POCKET_ID
    space.add(shape)
    



# ----------- SHOT EVALUTION -------------------------------------------

# EVALUATE ALL POSSIBLE SHOTS (FOR A GIVEN TABLE STATE)
# PARAMETERS: Table object
#             Pygame space obejct
# RETURNS:    Array of successful shot nodes (if they should continue to be evaluated), 
#             or None if current_shot_node is leaf node
# ASSUMES:
# 
# Define search space, angle and strength
# Loop through all search options:(double for loop of possible strength and angle possibilites)
#       Create new state of balls (create_initial_state) (or optionally, create a deep copy and pass to evaluate shot)
#       Call Evaluate shot
#       If shot made:
#           Add to array of successful shots
# Return array of successful shots to search tree algorithm          
def evaluate_all_possible_shots(current_shot_node: Node, space: pymunk.Space, shooting_team_id):
    angles = list(range(0, 360, 2))
    strengths = list(range(1000, 10000, 1000))
    valid_shot_nodes = []

    for angle in angles:
        print("Testing angle: " + str(angle))
        for strength in strengths:
            shot = evaluate_single_shot(space, strength, angle, current_shot_node.shot.table, shooting_team_id)
            if shot is not None:
                new_shot_node = Node(shot)
                new_shot_node.parent = current_shot_node
                new_shot_node.set_running_difficulty(shot.difficulty + new_shot_node.parent.running_difficulty)
                if best_running_difficulty == -1 or new_shot_node.running_difficulty < best_running_difficulty:
                    valid_shot_nodes.append(new_shot_node)
    return valid_shot_nodes
    
# EVALUATE SINGLE SHOT
# PARAMETERS: get_shot_diffulty (bool), space, force, angle, array of balls
# ASSUMES:
# RETURNS: shot object (if shot not made, return None)
# ---- BEGIN SIMULATION ----
# Possibly keep track of ball and wall bounces
# If ball made, set shot flag to to true
# ---- END SIMULATION ----
# If shot made flag, create Shot object, return shot object
def evaluate_single_shot(space: pymunk.Space, strength, angle, table: Table, shooting_team_id):
    balls_made = []
    legal = True
    first_contact_made = False

    def ball_in_pocket_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        balls_made.append(arbiter.shapes[0].id)
        print("Ball made: " + str(arbiter.shapes[0].id))
        space.remove(arbiter.shapes[0], arbiter.shapes[0].body)
        return False

    def scratch_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        legaility = False
        return False

    solids_pocket = space.add_collision_handler(SOLIDS_TEAM_ID, POCKET_ID)
    solids_pocket.begin = ball_in_pocket_handler
    stripes_pocket = space.add_collision_handler(STRIPES_TEAM_ID, POCKET_ID)
    stripes_pocket.begin = ball_in_pocket_handler
    scratch = space.add_collision_handler(CUE_BALL_ID, POCKET_ID)
    scratch.begin = scratch_handler
    cue_solid = space.add_collision_handler(CUE_BALL_ID, SOLIDS_TEAM_ID)
    cue_stripes = space.add_collision_handler(CUE_BALL_ID, STRIPES_TEAM_ID)

    x_force = strength * math.cos(angle * math.pi / 180)
    y_force = strength * math.sin(angle * math.pi / 180)

    cue = create_ball_at_location(table.balls[0].loc, space, 0)
    for index, ball in enumerate(table.balls):
        if index == 0:
            continue
        if ball is not None:
            create_ball_at_location(ball.loc, space, index)
    

    force_applied = False
    paused = True
    running = True
    pygame.init()
    screen = pygame.display.set_mode((1300, 800))
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    iter = 0
    if DRAW:
        while running:
            # Event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    paused = not paused

            if not paused:
                if not force_applied:
                    x_force = 10000
                    y_force = -10000
                    cue.body.apply_impulse_at_local_point((x_force, y_force), (0, 0)) # This is a single force being applied
                    force_applied = True

                screen.fill(pygame.Color("black"))
                space.debug_draw(draw_options)
                pygame.display.flip()
                fps = 60
                dt = 1.0 / fps
                for _ in range(100):
                    space.step(dt) # These can be modified to sped up the time scale
                clock.tick(fps)
    else:
        cue.body.apply_impulse_at_local_point((x_force, y_force), (0, 0)) # This is a single force being applied
        for _ in range(1000):
            space.step(1/60) # These can be modified to sped up the time scale
    
    shot = None
    if legal:
        new_table = Table(table.balls[:])
        for ball in balls_made:
            new_table.balls[ball] = None
        shot = Shot(new_table, angle, strength, 50)
    
    for joint in space.constraints:
        space.remove(joint)

    for shape in space.shapes:
        if shape.body.body_type == pymunk.Body.DYNAMIC:
            shot.table.balls[shape.id] = shape.body.position
            space.remove(shape)
    return shot

    

# GET SHOT DIFFICULTY
# PARAMETERS: 
# ASSUMES:
# REQUIRES:
# ----------- SHOT EVALUTION -------------------------------------------



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
    space = pymunk.Space()
    space.gravity = 0, 0
    
    
    # WALLS ARE ASSUMED TO BE CREATED IN A CERTAIN ORDER, FOR POCKET GENERATION
    walls: List[pymunk.Shape] = []
    walls.append(create_wall([(100, 50), (600, 50), (602, 40), (90, 40)], space))
    walls.append(create_wall([(650, 50), (1150, 50), (1160, 40), (648, 40)], space))
    walls.append(create_wall([(60, 90), (60, 590), (50, 600), (50, 80)], space))
    walls.append(create_wall([(1190, 90), (1190, 590), (1200, 600), (1200, 80)], space))
    walls.append(create_wall([(100, 630), (600, 630), (602, 640), (90, 640)], space))
    walls.append(create_wall([(650, 630), (1150, 630), (1160, 640), (648, 640)], space))

    # Triggers for detecting balls entering pockets
    pockets: List[pymunk.Shape] = []
    pockets.append(create_pocket((40, 40), 15, space))
    pockets.append(create_pocket((1190, 40), 15, space))
    pockets.append(create_pocket((615, 30), 15, space))
    pockets.append(create_pocket((40, 640), 15, space))
    pockets.append(create_pocket((615, 640), 15, space))
    pockets.append(create_pocket((1190, 640), 15, space))


    # 2 balls, 1 cue ball on table (assume 2 balls are for the same team)
    cue_ball = Ball(0, 0, (500, 500))
    ball1 = Ball(1, 3, (1000, 100))
    ball2 = Ball(1, 7, (850, 400))
    ball3 = Ball(1, 11, (200, 500))

    all_balls = [None] * 16
    all_balls[0] = cue_ball
    all_balls[3] = ball1
    all_balls[7] = ball2
    all_balls[11] = ball3

    table = Table(all_balls)
    shooting_team = SOLIDS_TEAM_ID
    initial_shot = Shot(table, 0, 0, 0)

    initial_shot_node = Node(initial_shot)

    # Evaluate 1 best shot
    shot_node_queue = queue.Queue()
    shot_node_queue.put(initial_shot_node)

    # Evalute all remaining
    global best_running_difficulty
    best_shot_node = None

    while shot_node_queue.empty() is False:
        print("QUEUE SIZE: " + str(shot_node_queue.qsize()))
        shot_node_to_eval = shot_node_queue.get()
        
        # Call eval shots
        optional_shot_nodes = evaluate_all_possible_shots(shot_node_to_eval, space, shooting_team)
        for node in optional_shot_nodes:
            if not node.shot.table.game_won:
                shot_node_queue.put(node)
            else:
                if best_shot_node is None or best_shot_node.running_difficulty > node.running_difficulty:
                    best_shot_node = node
                    best_running_difficulty = node.running_difficulty

    print(best_shot_node.running_difficulty)
    print("loop finished")


if __name__ == "__main__":
    main()