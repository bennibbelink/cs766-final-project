import pymunk
import pymunk.pygame_util
from typing import List
import pygame
import math
import queue
import copy
import vision
import numpy
from collections import deque

from statistics import mean

SHOT_ID_COUNTER = 0
SOLIDS_TEAM_ID= 0
STRIPES_TEAM_ID = 1
CUE_BALL_ID = 2
POCKET_ID = 3
WALL_ID = 4
EIGHT_BALL_ID = 5
SIZE_FACTOR = 10
BALL_SIZE = 1.125 * SIZE_FACTOR


best_running_difficulty = -1
    
class Ball:
    def __init__(self, team, label, loc):
        self.team = team
        self.label = label
        self.loc = loc

class Table:
    def __init__(self, balls: List[Ball]):
        self.balls = balls[:] # Array of class Ball
        self.game_won = False

class Shot: # only created after ball has been made
    def __init__(self, initial_table: Table, end_table: Table, angle, strength, difficulty, num_collisions):
        self.angle = angle
        self.strength = strength
        self.difficulty = difficulty
        self.initial_table = copy.deepcopy(initial_table) # initial state (before shot is taken)
        self.end_table = copy.deepcopy(end_table) # initial state (before shot is taken)
        self.num_collisions = num_collisions

        global SHOT_ID_COUNTER
        self.shot_id = SHOT_ID_COUNTER
        SHOT_ID_COUNTER += 1

class Node:
    def __init__(self, shot: Shot):
        self.parent = None
        self.shot = copy.deepcopy(shot)
        self.running_difficulty = 0

    def set_running_difficulty(self, diff):
        self.running_difficulty = diff


def simulate_shot(shot: Shot, space: pymunk.Space):
    force_applied = False
    paused = True
    running = True
    pygame.init()
    screen = pygame.display.set_mode((1300, 800))
    clock = pygame.time.Clock()
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    num_collisions = 0
    current_ball_index = 0
    legal = True
    shooting_team_id = SOLIDS_TEAM_ID

    cue = create_ball_at_location(shot.initial_table.balls[0].loc, space, 0)
    for index, ball in enumerate(shot.initial_table.balls):
        if index == 0:
            continue
        if ball is not None:
            create_ball_at_location(ball.loc, space, index)

    def ball_in_pocket_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        space.remove(arbiter.shapes[0], arbiter.shapes[0].body, arbiter.shapes[0].pivot)
        return False
    
    def cue_bank_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal num_collisions
        if current_ball_index == 0: 
            num_collisions += 1.5
            # print("number of collisions" +str(num_collisions))       
        return True

    def first_ball_hit_handler_solids(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal current_ball_index
        nonlocal num_collisions
        # print(str(current_ball_index) + "(first)")
        if current_ball_index == 0:       
            if shooting_team_id != SOLIDS_TEAM_ID:
                nonlocal legal
                legal = False
                # print(str(arbiter.shapes[1].id) + "(wrong team)")
                return False
            else: 
                current_ball_index = arbiter.shapes[1].id #data
                num_collisions = 1
                # print(str(current_ball_index) + "(update first ball hit)")
                return True 
        if current_ball_index == arbiter.shapes[1].id:  #account for a double hit
            legal = False
            return False
        return True
    

    solids_pocket = space.add_collision_handler(SOLIDS_TEAM_ID, POCKET_ID)
    solids_pocket.begin = ball_in_pocket_handler
    stripes_pocket = space.add_collision_handler(STRIPES_TEAM_ID, POCKET_ID)
    stripes_pocket.begin = ball_in_pocket_handler
    cue_bank = space.add_collision_handler(CUE_BALL_ID, WALL_ID) 
    cue_bank.begin = cue_bank_handler
    cue_solids = space.add_collision_handler(CUE_BALL_ID, SOLIDS_TEAM_ID)
    cue_solids.begin = first_ball_hit_handler_solids
    

    while running:
        
        if not paused and running:
            if not force_applied:
                strength = shot.strength
                angle = shot.angle
                x_force = strength * math.cos(angle * math.pi / 180)    
                y_force = strength * math.sin(angle * math.pi / 180)
                cue.body.apply_impulse_at_local_point((x_force, y_force), (0, 0)) # This is a single force being applied
                force_applied = True

            screen.fill(pygame.Color("black"))
            space.debug_draw(draw_options)
            pygame.display.flip()
            fps = 60
            dt = 1.0 / fps
            space.step(dt) # These can be modified to sped up the time scale
            clock.tick(fps)
        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                # pygame.display.quit()
                # pygame.quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                paused = not paused
            if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                running = False


# Method to create a ball at a location.
def create_ball_at_location(point, space, id):
    body = pymunk.Body()
    body.position = point[0], point[1]
    shape = pymunk.Circle(body, BALL_SIZE)
    shape.mass = 1
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
    pivot.max_force = 400
    shape.pivot = pivot
    return shape


# Method to create the walls inside the space. Eiter 2 points can be provided, which will be assumed
# to siginify the two inside boundaries, or 4 points will be provided to define a quadrilateral of 
# the wall,
def create_wall(points, space):
    if len(points) == 2:
        raise NotImplementedError
    elif len(points) == 4:
        print(points)
        shape = pymunk.Poly(space.static_body, [(points[0][0], points[0][1]), (points[1][0], points[1][1]), (points[2][0], points[2][1]), (points[3][0], points[3][1])])
        shape.collision_type = WALL_ID
        shape.elasticity = 1
        shape.color = (255, 255, 255, 255)
        space.add(shape)
        return shape
    else:
        raise ValueError


# Create triggers that balls collide with that will delete them
def create_pocket(points, space):
    # shape = pymunk.Poly(space.static_body, [top_left_corner,
    #     (top_left_corner[0], top_left_corner[1] + length),
    #     (top_left_corner[0] + length, top_left_corner[1] + length), 
    #     (top_left_corner[0] + length, top_left_corner[1])])
    shape = pymunk.Segment(space.static_body, (points[0][0], points[0][1]), (points[1][0], points[1][1]), 1) 
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
    angles = list(range(0, 360, 1))
    strengths = list(range(100, 1201, 200))
    valid_shot_nodes = []

    for angle in angles:
        for strength in strengths:
            shot = evaluate_single_shot(space.copy(), strength, angle, current_shot_node.shot.end_table, shooting_team_id)
            if shot is not None:
                new_shot_node = Node(shot)
                new_shot_node.parent = current_shot_node
                new_shot_node.set_running_difficulty(shot.difficulty + new_shot_node.parent.running_difficulty)
                if best_running_difficulty == -1 or new_shot_node.running_difficulty < best_running_difficulty:
                    valid_shot_nodes.append(new_shot_node)
    # for node in valid_shot_nodes:
    #     simulate_shot(node.shot, copy.deepcopy(space))
    #     print("shot stats")
    #     print(node.shot.shot_id)
    #     print(node.shot.difficulty)
    #     print(node.running_difficulty)
    #     print(node.shot.strength)
    #     print(node.shot.angle)
    #     print(node.shot.num_collisions)
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
    pocket_made_loc = []
    legal = True
    current_ball_index = 0
    num_collisions = 0
    shot_difficulty = 0

    def ball_in_pocket_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        balls_made.append(arbiter.shapes[0].id)
        pocket_made_loc.append(arbiter.shapes[1].center_of_gravity)
        # print("Ball made: " + str(arbiter.shapes[0].id) + " -- " + str(arbiter.shapes[1].center_of_gravity))
        space.remove(arbiter.shapes[0], arbiter.shapes[0].body, arbiter.shapes[0].pivot)
        return False

    def scratch_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal legal
        legal = False
        return False
    
    def eight_ball_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data): 
        nonlocal current_ball_index
        nonlocal num_collisions
        if current_ball_index == 0:
            num_collisions += 8        # Temp Solution Need to address shot on the 8-ball
        return True
    
    def first_ball_hit_handler_solids(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal current_ball_index
        nonlocal num_collisions
        # print(str(current_ball_index) + "(first)")
        if current_ball_index == 0:       
            if shooting_team_id != SOLIDS_TEAM_ID:
                nonlocal legal
                legal = False
                # print(str(arbiter.shapes[1].id) + "(wrong team)")
                return False
            else: 
                current_ball_index = arbiter.shapes[1].id #data
                num_collisions +=1
                # print(str(current_ball_index) + "(update first ball hit)")
                return True 
        if current_ball_index == arbiter.shapes[1].id:  #account for a double hit
            legal = False
            return False
        return True
    
    def first_ball_hit_handler_stripes(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal current_ball_index
        nonlocal num_collisions
        nonlocal legal
        # print(str(current_ball_index) + "(first)")
        if current_ball_index == 0:       
            if shooting_team_id != STRIPES_TEAM_ID:
                legal = False
                # print(str(arbiter.shapes[1].id) + "(wrong team)")
                return False
            else: 
                current_ball_index = arbiter.shapes[1].id #data
                num_collisions = 1
                # print(str(current_ball_index) + "(update first ball hit)")
                return True 
        if current_ball_index == arbiter.shapes[1].id:
            legal = False
            return False
        return True
             
    def combo_ball_hit_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal current_ball_index
        nonlocal num_collisions
        if arbiter.shapes[0].id == current_ball_index or arbiter.shapes[1].id == current_ball_index:
            num_collisions += 1
            # print(num_collisions)
            return True
        else:
            return True
    
    def cue_bank_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal num_collisions
        if current_ball_index == 0: 
            num_collisions += 1.5     
        return True
    
    def bank_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data):
        nonlocal num_collisions
        if arbiter.shapes[0].id == current_ball_index: 
            num_collisions += 1
        return True

    
    solids_pocket = space.add_collision_handler(SOLIDS_TEAM_ID, POCKET_ID)
    solids_pocket.begin = ball_in_pocket_handler
    stripes_pocket = space.add_collision_handler(STRIPES_TEAM_ID, POCKET_ID)
    stripes_pocket.begin = ball_in_pocket_handler
    scratch = space.add_collision_handler(CUE_BALL_ID, POCKET_ID)
    scratch.begin = scratch_handler
    cue_solids = space.add_collision_handler(CUE_BALL_ID, SOLIDS_TEAM_ID)
    cue_solids.begin = first_ball_hit_handler_solids
    cue_stripes = space.add_collision_handler(CUE_BALL_ID, STRIPES_TEAM_ID)
    cue_stripes.begin = first_ball_hit_handler_stripes
    combo_solids = space.add_collision_handler(SOLIDS_TEAM_ID, SOLIDS_TEAM_ID) 
    combo_solids.begin = combo_ball_hit_handler
    combo_stripes = space.add_collision_handler(STRIPES_TEAM_ID, STRIPES_TEAM_ID) 
    combo_stripes.begin = combo_ball_hit_handler
    cue_bank = space.add_collision_handler(CUE_BALL_ID, WALL_ID) 
    cue_bank.begin = cue_bank_handler
    solids_bank = space.add_collision_handler(SOLIDS_TEAM_ID, WALL_ID)
    solids_bank.begin = bank_handler
    stripes_bank = space.add_collision_handler(STRIPES_TEAM_ID, WALL_ID) 
    stripes_bank.begin = bank_handler
    eight_ball = space.add_collision_handler(CUE_BALL_ID, EIGHT_BALL_ID)
    eight_ball.begin = eight_ball_handler
    
    
    x_force = strength * math.cos(angle * math.pi / 180)    
    y_force = strength * math.sin(angle * math.pi / 180)

    cue = create_ball_at_location(table.balls[0].loc, space, 0)
    for index, ball in enumerate(table.balls):
        if index == 0:
            continue
        if ball is not None:
            create_ball_at_location(ball.loc, space, index)

    cue.body.apply_impulse_at_local_point((x_force, y_force), (0, 0)) # This is a single force being applied
    for _ in range(1000):
        space.step(1/60) # These can be modified to sped up the time scale
    shot = None
    for ball in balls_made:
        if (ball <= 7 and shooting_team_id != SOLIDS_TEAM_ID) or (ball > 7 and shooting_team_id != STRIPES_TEAM_ID):
            legal = False

    if legal and len(balls_made) != 0: 
        new_table = Table(table.balls[:])   
        for ball in balls_made:
            new_table.balls[ball] = None
        for index, ball in enumerate(balls_made): 
            cue_to_obj = math.dist(table.balls[0].loc, table.balls[ball].loc) 
            obj_to_pock = math.dist(table.balls[ball].loc, pocket_made_loc[index]) 
            # get_angle
            v1 = (pocket_made_loc[index][0] - table.balls[ball].loc[0], pocket_made_loc[index][1] - table.balls[ball].loc[1])
            v2 = (table.balls[ball].loc[0] - table.balls[0].loc[0], table.balls[ball].loc[1] - table.balls[0].loc[1])
            dif_angle = math.degrees(math.acos(numpy.dot(v1, v2) / (obj_to_pock * cue_to_obj)))
            shot_difficulty += get_shot_difficulty(cue_to_obj / SIZE_FACTOR, obj_to_pock / SIZE_FACTOR, dif_angle, num_collisions)
            
            
        shot = Shot(table, new_table, angle, strength, shot_difficulty, num_collisions) 
        
        # print("Legal Shot:" + str(balls_made) + str(shot.shot_id))
        if all(v is None for v in new_table.balls[1:8]):
            shot.end_table.game_won = True
            # print("GAME WON")
    
    for joint in space.constraints:
        space.remove(joint)

    for body in space.bodies:
        if body.body_type == pymunk.Body.DYNAMIC:  
            if legal and len(balls_made) != 0:
                shot.end_table.balls[list(body.shapes)[0].id].loc = body.position
            space.remove(list(body.shapes)[0], body)
    return shot

    

# GET SHOT DIFFICULTY
# PARAMETERS: angle = 
# ASSUMES: 
# REQUIRES: 
def get_shot_difficulty(cue_to_object, object_to_pocket, angle, collisions_involved):
    
    # print("-- shot difficulty --")
    # print(cue_to_object)
    # print(object_to_pocket)
    # print(angle)
    if angle > 90:
        angle = 180 - angle
        collisions_involved += 1

    if collisions_involved == 1:
        collision_factor = 1
    else:
        collision_factor = 2 * (collisions_involved - 1)
    # print(collisions_involved)
    # print(cue_to_object)
    # print(object_to_pocket)
    # print(angle)
    difficulty = (math.cos(math.radians(angle)) / cue_to_object * object_to_pocket ) * collision_factor * 100
    # print(difficulty)
    return  difficulty 

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
    
    #Calculate the table dimensions
    table_width = 88
    table_height = 44
    

    rail_wid = 2 * SIZE_FACTOR
    sp_diff = .5 / 2 * SIZE_FACTOR
    cp_mouth_len = 3.2 * SIZE_FACTOR
    cp_throat_len = 2.9 * SIZE_FACTOR
    sp_throat_wid = 4.5 * SIZE_FACTOR

    start_x = 50
    top_rail_out_y = 50
    top_rail_in_y = 50 + rail_wid
    bot_rail_in_y = top_rail_in_y + table_height * SIZE_FACTOR
    bot_rail_out_y = bot_rail_in_y + rail_wid

    top_wall_outlen = (((table_width * SIZE_FACTOR) + (2 * cp_throat_len) - (2 * rail_wid) - (sp_throat_wid)) / 2) 
    side_wall_outlen = (table_height * SIZE_FACTOR) - (2 * cp_throat_len) + (2 * rail_wid)

    w1_p1 = (start_x + cp_throat_len, top_rail_out_y)
    w1_p2 = (w1_p1[0] + top_wall_outlen, top_rail_out_y)
    w1_p3 = (w1_p2[0] - sp_diff, top_rail_in_y)
    w1_p4 = (start_x + cp_mouth_len + rail_wid, top_rail_in_y)

    w2_p1 = (w1_p2[0] + sp_throat_wid, top_rail_out_y)
    w2_p2 = (w2_p1[0] + top_wall_outlen, top_rail_out_y)
    w2_p3 = (w2_p2[0] + cp_throat_len - cp_mouth_len - rail_wid, top_rail_in_y)
    w2_p4 = (w2_p1[0] + sp_diff, top_rail_in_y)

    w3_p1 = (w2_p2[0] + cp_throat_len, top_rail_out_y + cp_throat_len)
    w3_p2 = (w3_p1[0],  w3_p1[1] + side_wall_outlen)
    w3_p3 = (w3_p1[0] - rail_wid, w3_p2[1] + cp_throat_len - cp_mouth_len - rail_wid)
    w3_p4 = (w3_p3[0], w3_p1[1] - cp_throat_len + cp_mouth_len + rail_wid)

    w4_p1 = (start_x, top_rail_out_y + cp_throat_len)
    w4_p2 = (start_x, w4_p1[1] + side_wall_outlen)
    w4_p3 = (w4_p1[0] + rail_wid, w4_p2[1] + cp_throat_len - cp_mouth_len - rail_wid)
    w4_p4 = (w4_p3[0], w4_p1[1] - cp_throat_len +cp_mouth_len +rail_wid)

    w5_p1 = (start_x + cp_throat_len, bot_rail_out_y)
    w5_p2 = (w5_p1[0] + top_wall_outlen, bot_rail_out_y)
    w5_p3 = (w5_p2[0] - sp_diff, bot_rail_in_y)
    w5_p4 = (start_x + cp_mouth_len + rail_wid, bot_rail_in_y)

    w6_p1 = (w5_p2[0] + sp_throat_wid, bot_rail_out_y)
    w6_p2 = (w6_p1[0] + top_wall_outlen, bot_rail_out_y)
    w6_p3 = (w6_p2[0] + cp_throat_len -cp_mouth_len - rail_wid, bot_rail_in_y)
    w6_p4 = (w6_p1[0] + sp_diff, bot_rail_in_y)

    # half of the ball size
    hb = .5 * BALL_SIZE
    # h1 = (mean([w1_p1[0], w4_p1[0]]), mean([w1_p1[1], w4_p1[1]])) 
    # h2 = (mean([w1_p2[0], w2_p1[0]]), mean([w1_p2[1], w2_p1[1]]))
    # h3 = (mean([w2_p2[0], w3_p1[0]]), mean([w2_p2[1], w3_p1[1]]))
    # h4 = (mean([w6_p2[0], w3_p2[0]]), mean([w6_p2[1], w3_p2[1]]))
    # h5 = (mean([w5_p2[0], w6_p1[0]]), mean([w5_p2[1], w6_p1[1]]))
    # h6 = (mean([w4_p2[0], w5_p1[0]]), mean([w4_p2[1], w5_p1[1]]))
    
    h1_line = [(w4_p1[0]-hb, w4_p1[1]-hb), (w1_p1[0]-hb, w1_p1[1]-hb)]
    h2_line = [(w1_p2[0], w1_p2[1]-hb), (w2_p1[0], w2_p1[1]-hb)]
    h3_line = [(w2_p2[0]+hb, w2_p2[1]-hb), (w3_p1[0]+hb, w3_p1[1]-hb)]
    h4_line = [(w6_p2[0]+hb, w6_p2[1]+hb), (w3_p2[0]+hb, w3_p2[1]+hb)]
    h5_line = [(w5_p2[0], w5_p2[1]+hb), (w6_p1[0], w6_p1[1]+hb)]
    h6_line = [(w4_p2[0]-hb, w4_p2[1]+hb), (w5_p1[0]-hb, w5_p1[1]+hb)]

    ll = (start_x + rail_wid, bot_rail_in_y)
    ul = (ll[0], top_rail_in_y)
    lr = (w3_p3[0], bot_rail_in_y)
    ur = (lr[0], top_rail_in_y)
    
    # WALLS ARE ASSUMED TO BE CREATED IN A CERTAIN ORDER, FOR POCKET GENERATION
    walls: List[pymunk.Shape] = []
    walls.append(create_wall([w1_p1, w1_p2, w1_p3, w1_p4], space))
    walls.append(create_wall([w2_p1, w2_p2, w2_p3, w2_p4], space))
    walls.append(create_wall([w3_p1, w3_p2, w3_p3, w3_p4], space))
    walls.append(create_wall([w4_p1, w4_p2, w4_p3, w4_p4], space))
    walls.append(create_wall([w5_p1, w5_p2, w5_p3, w5_p4], space))
    walls.append(create_wall([w6_p1, w6_p2, w6_p3, w6_p4], space))
    # walls.append(create_wall([(100, 50), (600, 50), (602, 40), (90, 40)], space))
    # walls.append(create_wall([(650, 50), (1150, 50), (1160, 40), (648, 40)], space))
    # walls.append(create_wall([(60, 90), (60, 590), (50, 600), (50, 80)], space))
    # walls.append(create_wall([(1190, 90), (1190, 590), (1200, 600), (1200, 80)], space))
    # walls.append(create_wall([(100, 630), (600, 630), (602, 640), (90, 640)], space))
    # walls.append(create_wall([(650, 630), (1150, 630), (1160, 640), (648, 640)], space))

    # Triggers for detecting balls entering pockets
    pockets: List[pymunk.Shape] = []
    pockets.append(create_pocket(h1_line, space))
    pockets.append(create_pocket(h2_line, space))
    pockets.append(create_pocket(h3_line, space))
    pockets.append(create_pocket(h4_line, space))
    pockets.append(create_pocket(h5_line, space))
    pockets.append(create_pocket(h6_line, space))
    # pockets.append(create_pocket((40, 40), 15, space))
    # pockets.append(create_pocket((1190, 40), 15, space))
    # pockets.append(create_pocket((615, 30), 15, space))
    # pockets.append(create_pocket((40, 640), 15, space))
    # pockets.append(create_pocket((615, 640), 15, space))
    # pockets.append(create_pocket((1190, 640), 15, space))


    # 2 balls, 1 cue ball on table (assume 2 balls are for the same team)
    # cue_ball = Ball(0, 0, (100, 500))
    # ball1 = Ball(SOLIDS_TEAM_ID, 3, (100, 100))
    # ball2 = Ball(SOLIDS_TEAM_ID, 7, (170, 170))
    # ball3 = Ball(STRIPES_TEAM_ID, 11, (200, 500))

    # all_balls = [None] * 16
    # all_balls[0] = cue_ball
    # all_balls[3] = ball1
    # all_balls[7] = ball2
    # all_balls[11] = ball3

    all_balls = vision.get_balls(ll, ul, lr, ur).tolist()

    table = Table(all_balls)
    shooting_team = SOLIDS_TEAM_ID
    initial_shot = Shot(table, table, 0, 0, 0, 0)
    # initial_shot.angle = 320
    # initial_shot.strength = 1000
    initial_shot_node = Node(initial_shot)

    # Evaluate 1 best shot
    shot_node_queue = deque()
    shot_node_queue.append(initial_shot_node)

    # Evalute all remaining
    global best_running_difficulty
    best_shot_node = None

    while len(shot_node_queue) != 0:
        print("QUEUE SIZE: " + str(len(shot_node_queue)))
        shot_node_to_eval = shot_node_queue.pop()
        
        # Call eval shots
        optional_shot_nodes = evaluate_all_possible_shots(shot_node_to_eval, space.copy(), shooting_team)
        for node in optional_shot_nodes:
            if not node.shot.end_table.game_won:
                shot_node_queue.append(node)
            else:
                if best_shot_node is None or best_shot_node.running_difficulty > node.running_difficulty:
                    best_shot_node = node
                    best_running_difficulty = node.running_difficulty
    if best_shot_node is None:
        print("No way to win game!")
    else:
        print(best_shot_node.running_difficulty)
        curr_node = best_shot_node
        shot_sequence = []
        while curr_node.parent is not None:
            shot_sequence.insert(0, curr_node.shot)
            curr_node = curr_node.parent
        
        for shot in shot_sequence:
            simulate_shot(shot, space.copy())
        

if __name__ == "__main__":
    main()