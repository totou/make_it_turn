import sys
import math

def solv_equa(x,a,b,c):
    return a*x**2+x*b+c

def solver_x2(p1,p2,p3):
    #return a,b,c such as for 3 point Y = aX**2 + bX + c
    # check point are different
    def coeff(p):
        return {'r':p.y,'a':p.x**2,'b':p.x,'c':1}
    equ1 = [coeff(p1),coeff(p2),coeff(p3)]
    #Reduction to one equation
    #p1-p2 -> p4
    equ2 = []
    equ2.append({'r':equ1[0]['r']*equ1[1]['c']-equ1[1]['r']*equ1[0]['c'],
                 'a':equ1[0]['a']*equ1[1]['c']-equ1[1]['a']*equ1[0]['c'],
                 'b':equ1[0]['b']*equ1[1]['c']-equ1[1]['b']*equ1[0]['c'],
                 'c':0})
    #p2-p3 -> p5
    equ2.append({'r':equ1[1]['r']*equ1[2]['c']-equ1[2]['r']*equ1[1]['c'],
                 'a':equ1[1]['a']*equ1[2]['c']-equ1[2]['a']*equ1[1]['c'],
                 'b':equ1[1]['b']*equ1[2]['c']-equ1[2]['b']*equ1[1]['c'],
                 'c':0})
    #p4-p5
    equ3 = [{'r':equ2[0]['r']*equ2[1]['b']-equ2[1]['r']*equ2[0]['b'],
             'a':equ2[0]['a']*equ2[1]['b']-equ2[1]['a']*equ2[0]['b'],
             'b':0,
             'c':0}]
    a=equ3[0]['r'] / equ3[0]['a']
    b=(equ2[0]['r'] - equ2[0]['a'] * a) / equ2[0]['b']
    c=(equ1[0]['r'] - equ1[0]['a'] * a - equ1[0]['b'] * b) / equ1[0]['c']

    return a, b, c

class Pod(object):
    def __init__(self, x, y, vx, vy, angle, target_checkpoint, score=0, rank=None):
        self._x = x
        self._y = y
        self.p = Point(x, y)
        self.vx = vx
        self.vy = vy
        self.v = Vector(vx, vy)
        self.angle = angle
        self.target_id = target_checkpoint
        self.score = score
        #for 1 to 4 depending on position
        self.rank = rank
        self.behaviour = "race" # Default behaviour is race

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = val
        self.p.x = val

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = val
        self.p.y = val

    @property
    def target(self):
        return global_checkpoints[self.target_id]

    @property
    def next_target_id(self):
        if self.target_id < len(global_checkpoints)-1:
            return self.target_id + 1
        else:
            return 0

    @property
    def next_target(self):
        if self.target_id < len(global_checkpoints)-1:
            if self.is_last_checkpoint():
                return global_checkpoints[self.target_id]
            else:
                return global_checkpoints[self.target_id + 1]
        else:
            return global_checkpoints[0]

    def angle_between_speed_and_curr_target(self):
        curr_dir = Vector(100*math.cos(math.radians(self.angle)), 100*math.sin(math.radians(self.angle)))
        direction_to_take = self.next_target - self.target
        #print(self.v, file=sys.stderr)
        #print((self.target - self.p).to_Point(), file=sys.stderr)
        r = Point(0, 0).angle_three_point(self.v.to_Point(), (self.target - self.p).to_Point())
        #print("Angle between speed {} and target {} is {} degrees".format(self.v, self.target_id, r), file=sys.stderr)
        return r


    def angle_to_make_for_next_target(self):
        curr_dir = Vector(100*math.cos(math.radians(self.angle)), 100*math.sin(math.radians(self.angle)))
        direction_to_take = self.next_target - self.target
        return Point(0, 0).angle_three_point(curr_dir.to_Point(), direction_to_take.to_Point())

    def turn_needed_to_orientate_to_next_checkpoint(self):
        return max(0, math.ceil(self.angle_to_make_for_next_target()/global_max_rotation))

    def is_last_checkpoint(self):
        return self.score == global_laps*len(global_checkpoints)-1

    def get_distance_checkpoint(self, checkpoint_id=None):
        if checkpoint_id is None:
            checkpoint_id = self.target_id
        return self.p.get_distance(global_checkpoints[checkpoint_id])

    def set_rank(self, pods):
        self.rank = 1
        for pod in pods:
            if pod != self:
                if pod.score > self.score:
                    self.rank += 1
                if pod.score == self.score and self.get_distance_checkpoint() > pod.get_distance_checkpoint():
                    self.rank += 1

    def get_num_tour_to_target(self, target=None):
        """Talking in speed only, not direction..."""
        if target is None:
            target = global_checkpoints[self.target_id]
        if self.v.get_norm() > 0:
            return int(self.p.get_distance(target) / self.v.get_norm())
        else:
            return int(100)

    def will_reach_target_in_rounds(self, num_rounds,checkpoint_size,target=None):
        if target is None:
            target = self.target
        speed = self.v
        next_point = self.p
        for i in range(num_rounds):
            next_point += speed * math.pow(global_vattenuation, i)
            if target.get_distance(next_point) < checkpoint_size:
                return True, i+1
        return False, 0

    def calculate_new_thrust(self,num_rounds, checkpoint_size=600, attack_angle=0):
        max_speed = 200
        if global_turn==0:
            return max_speed
        if self.activate_shield():
            return "SHIELD"
        if self.get_angle_to_target() > attack_angle:
            print('Angle too big do not thust: {}'.format(self.get_angle_to_target()), file=sys.stderr)
            return 0
        can_reach, nb = self.will_reach_target_in_rounds(num_rounds,checkpoint_size)
        if can_reach and nb <= num_rounds:
            if self.is_last_checkpoint():
                return max_speed
            #someone in the way -> CHAAAARGE
            for i in range(nb):
                my_pos = self.next_position(i)
                for pod in global_my_pods+global_ennemy_pods:
                    if pod != self:
                        if pod.next_position(i).get_distance(my_pos) < 800:
                            return max_speed
            #check thrust to still pass in checkpoint
            next_checkpoint=global_checkpoints[get_next_target_id(self.target)]
            pod_list_thrust=[[self.next_pod(next_checkpoint,x),x]  for x in range(max_speed,-1,-20)]
            # print('pod_list_thrust {}'.format(pod_list_thrust), file=sys.stderr)
            for pod_t, thrust in pod_list_thrust:
                can_reach_t, _ = pod_t.will_reach_target_in_rounds(num_rounds-1,checkpoint_size)
                # print('Reach {}, thrust {}'.format(can_reach_t,thrust), file=sys.stderr)
                if can_reach_t:
                    return thrust
            print('already going to checkpoint', file=sys.stderr)
            return 0
            #return int(max_speed * nb / 5)
        if self.get_num_tour_to_target() < global_will_reach_target:
            return 0
        return max_speed

    def next_pod_for_destination(self, destination, thrust):
        #first find angle
        cur_proj = self.p.get_transposed_from_angle(self.angle, 10)
        next_proj = destination
        rotation = self.p.angle_three_point_signed(cur_proj, next_proj)
        if rotation > global_max_rotation:
            rotation = global_max_rotation
        if rotation < -global_max_rotation:
            rotation = -global_max_rotation
        return self.next_pod_with_angle(rotation, thrust)

    def next_pod_with_angle(self, rotation, thrust):
        angle = self.angle+rotation

        vx = self.vx+thrust*math.cos(math.radians(self.angle))
        vy = self.vy+thrust*math.sin(math.radians(self.angle))

        x = self.x+vx
        y = self.y+vy

        vx *= global_vattenuation
        vy *= global_vattenuation

        checkpoint_id = self.target_id
        score = self.score
        return Pod(x, y, vx, vy, angle, checkpoint_id, score)

    def next_position(self, n=1):
        return Point(self.p.x + self.v.x*global_vattenuation**(n-1), self.p.y + self.v.y*global_vattenuation**(n-1))

    def activate_shield(self):
        for pod in global_my_pods+global_ennemy_pods:
            if pod != self:
                if pod.next_position().get_distance(self.next_position()) < 800:
                    #check speed to validate vmax ?
                    if pod.v.get_norm()+self.v.get_norm() < global_vmax*0.2:
                        return False
                    #check angle
                    if Point(0, 0).angle_three_point(pod.v.to_Point(), self.v.to_Point()) < 25:
                        return False
                    print("Activate SHIELD", file=sys.stderr)
                    return True
        return False

    def get_angle_to_target(self, targeting=None):
        if targeting is None:
            targeting = self.target
        new = self.p.get_transposed_from_angle(self.angle)
        return self.p.angleThreePoint(new, targeting)

    def __str__(self):
        res = ''
        # res+="Point {0}\n".format(self.p)
        # res+="Vitesse {0}\n".format(self.v)
        # res+="Angle {0}\n".format(self.angle)
        # res+="Checkpoint {0}\n".format(self.target)
        # res+="Score {0}\n".format(self.score)
        # res+="Rank {0}\n".format(self.rank)
        return res

    # def goto(self, point, angle, speed):
    #     #line between two points
    #     #line


class Vector(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __radd__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __rsub__(self, other):
        return Vector(other.x - self.x, other.y - self.y)

    def __mul__(self, other):
        return Vector(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def get_norm(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def get_norm_to_target(self, target):# TODO check this function
        angle_with_target = Point(0, 0).angle_three_point_signed(self.to_Point(), target)
        return self.get_norm() * math.cos(math.radians(angle_with_target))

    def to_Point(self):
        return Point(self.x, self.y)

    def __str__(self):
        res = "Vector({},{})".format(self.x, self.y)
        return res


class Point(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __rsub__(self, other):
        return Vector(other.x - self.x, other.y - self.y)

    def get_distance(self, p):
        return math.sqrt((self.x - p.x) ** 2 + (self.y - p.y) ** 2)


    def closest(self, list_p):
        dist_list = map(self.get_distance, list_p)
        return dist_list.index(min(dist_list))

    def add_vector(self, v):
        return Point(self.x + v.x, self.y + v.y)

    def __repr__(self):
        return '{0} {1}'.format(int(self.x), int(self.y))

    def get_transposed(self, t, dist_max):
        return self.get_transposed_from_point(t.p, dist_max)

    def get_transposed_from_point(self, p, dist_max):
        dist_t = self.get_distance(p)
        if dist_max < dist_t:
            x = min(max(int(math.floor(self.x + (p.x - self.x) * dist_max / dist_t)), 0), 16000)
            y = min(max(int(math.floor(self.y + (p.y - self.y) * dist_max / dist_t)), 0), 9000)
            return Point(x, y)
        else:
            return p

    def get_transposed_from_angle(self, angle_degree, dist_max=1):
        rad = math.radians(angle_degree)
        x = self.x+dist_max*math.cos(rad)
        y = self.y+dist_max*math.sin(rad)
        return Point(x, y)

    def angle_three_point(self, point1, point2):
        do1 = self.get_distance(point1)
        do2 = self.get_distance(point2)
        d12 = point1.get_distance(point2)
        if do1 == 0 or do2 == 0:
            return 0
        return math.degrees(math.acos((do1**2+do2**2-d12**2)/(2*do1*do2)))

    def angle_three_point_signed(self, point1, point2):
        #same thing but with signed on angle this time
        #copy paste stack untested
        a = point1.x - self.x
        b = point1.y - self.y
        c = point1.x - point2.x
        d = point1.y - point2.y

        atanA = math.atan2(a, b)
        atanB = math.atan2(c, d)

        return math.degrees(atanB - atanA)

    def get_circle(self, dist_max, division=400):
        res = []
        for x in range(self.x - dist_max, self.x + dist_max, division):
            res.append(Point(x, self.y - dist_max))
        for x in range(self.x - dist_max, self.x + dist_max, division):
            res.append(Point(x, self.y + dist_max))
        for y in range(self.y - dist_max, self.y + dist_max, division):
            res.append(Point(self.x - dist_max, y))
        for y in range(self.y - dist_max, self.y + dist_max, division):
            res.append(Point(self.x + dist_max, y))
        return list(set([self.get_transposed_from_point(p, dist_max) for p in res]))


def get_next_target_id(current_target_index):
    if current_target_index < len(global_checkpoints)-1:
        return current_target_index+1
    else:
        return 0


def get_first_pod():
    for pod in global_my_pods+global_ennemy_pods:
        if pod.rank == 1:
            return pod


standard_runner={'checkpoint_size':550, 'turn_to_turn':5, 'angle_to_speed':45}
agressive_runner={'checkpoint_size':550, 'turn_to_turn':5, 'angle_to_speed':45}
# agressive_runner={'checkpoint_size':600, 'turn_to_turn':4, 'angle_to_speed':45}

def runner(pod, agressive=False):
    print("I am a runner", file=sys.stderr)
    behavior_dict=standard_runner
    if agressive:
        behavior_dict=agressive_runner

    curr_target = pod.target
    next_target = pod.next_target
    checkpoint_size = behavior_dict['checkpoint_size']
    angle_to_speed = curr_target.angleThreePoint(pod.p,next_target)
    num_turn = max(1,math.ceil(angle_to_speed/global_max_rotation))
    curr_vect = curr_target - pod.p
    next_vect = next_target - pod.p
    #print("Target n is at {}".format(curr_vect.get_norm()), file=sys.stderr)
    #print("Target n+1 is at {}".format(next_vect.get_norm()), file=sys.stderr)
    curr_norm = curr_vect.get_norm()
    next_norm = next_vect.get_norm()
    speed = pod.calculate_new_thrust(num_turn, checkpoint_size, angle_to_speed)
    can_reach, number = pod.will_reach_target_in_rounds(num_turn, checkpoint_size)
    if not can_reach or pod.is_last_checkpoint():
        new_target = pod.p.add_vector(curr_vect - pod.v * min(num_turn,max(1,(pod.get_num_tour_to_target()-1))) )
        print("{} {} {}".format(new_target.x, new_target.y, speed))
    else:
        print("{} {} {}".format(next_target.x, next_target.y, speed))


global_bruiser_state = 'defense'
def bruiser(pod):
    global global_bruiser_state
    print("I am a buiser", file=sys.stderr)
    #track ennemy pod
    pod_target = global_ennemy_pods[0] if global_ennemy_pods[0].rank < global_ennemy_pods[1].rank else global_ennemy_pods[1]
    enemy_checkpoint = global_checkpoints[pod_target.target]
    curr_target = enemy_checkpoint
    if pod_target.p.get_distance(enemy_checkpoint) < pod.p.get_distance(enemy_checkpoint):
        global_bruiser_state = 'defense'
        curr_target = global_checkpoints[get_next_target_id(pod_target.target)]
    else:
        global_bruiser_state = 'attack'
    checkpoint_size = 600

    if pod.p.get_distance(curr_target) < checkpoint_size or global_bruiser_state=='attack':
        print("Bruiser on target", file=sys.stderr)
        speed=0
        n=0
        if pod_target.v.get_norm()!=0:
            n=int(pod.p.get_distance(pod_target.p)/pod_target.v.get_norm())
        extrapolate_target = Point(int(pod_target.p.x+pod_target.v.x+pod_target.v.x*0.85**n), int(pod_target.p.y+pod_target.v.y+pod_target.v.y*0.85**n))
        if pod.activate_shield():
            speed = 'SHIELD'
        elif pod.p.get_distance(pod_target.p) <  4000 and pod.get_angle_to_target(extrapolate_target) > 18:
            speed = 200
        print("{} {} {}".format(extrapolate_target.x, extrapolate_target.y, speed))

    else:
        # go and stop on checkpoint
        print("Bruiser going to checkpoint", file=sys.stderr)
        angle_to_speed = curr_target.angleThreePoint(pod.p,pod_target.p)
        num_turn = int(angle_to_speed/global_max_rotation)*2
        curr_vect = curr_target - pod.p
        can_reach, number = pod.will_reach_target_in_rounds(num_turn, checkpoint_size, curr_target)
        if not can_reach:
            speed = 200
            if pod.get_angle_to_target(curr_target) > 18:
                speed=0
            new_target = pod.p.add_vector(curr_vect - pod.v * min(num_turn,max(1,(pod.get_num_tour_to_target(curr_target)-1))) )
            print("{} {} {}".format(new_target.x, new_target.y, speed))
        else:
            print("{} {} {}".format(pod_target.p.x+pod_target.v.x, pod_target.p.y+pod_target.v.y, 0))

global_bruiser_state = 'position'
def helper(pod):
    pod_partner = [x for x in global_my_pods if x != pod][0]



def pick_Behavior(pod,friend):
    agressive = True
    if pod.rank==1:
        agressive = False

    if pod.rank < friend.rank:
        runner(pod,agressive=agressive)
    # elif pod.rank == 2:
    #     #agressive
    #     runner(pod,agressive=agressive)
    # elif pod.score > get_first_pod().score -2:
    #     # (very ?) agressive
    #     runner(pod,agressive=agressive)
    else:
        # bruiser(pod)
        runner(pod,agressive=agressive)

global_vmax = 1200
global_vattenuation = 0.85
global_max_rotation = 18
global_my_pods = [None, None]
global_ennemy_pods = [None, None]
global_checkpoints = []
global_will_reach_target = 5

# Auto-generated code below aims at helping you parse
# the standard input according to the problem statement.

global_laps = int(input())
checkpoint_count = int(input())
for i in range(checkpoint_count):
    cx, cy = [int(j) for j in input().split()]
    global_checkpoints.append(Point(cx, cy))

if checkpoint_count != len(global_checkpoints):
    print("Error, bad checkpoint input")

# game loop
global_turn = 0
while True:
    for i in range(2):
        x, y, vx, vy, angle, nextCheckPointId = [int(j) for j in input().split()]
        if global_turn == 0:
            global_my_pods[i] = Pod(x, y, vx, vy, angle, nextCheckPointId)
        else:
            if nextCheckPointId != global_my_pods[i].target_id:
                global_my_pods[i].score += 1
            global_my_pods[i] = Pod(x, y, vx, vy, angle, nextCheckPointId, score=global_my_pods[i].score)
    for i in range(2):
        x, y, vx, vy, angle, next_check_point_id = [int(j) for j in input().split()]
        if global_turn == 0:
            global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id)
        else:
            if next_check_point_id != global_ennemy_pods[i].target_id:
                global_ennemy_pods[i].score += 1
            global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id, score=global_ennemy_pods[i].score)

    all_pod = global_my_pods+global_ennemy_pods
    for pod in all_pod:
        pod.set_rank(all_pod)
        # print(pod, file=sys.stderr)
        # print(solver_x2(pod.p,global_checkpoints[pod.target],global_checkpoints[get_next_target_id(pod.target)]), file=sys.stderr)

    # To debug: print("Debug messages...", file=sys.stderr)

    pick_Behavior(global_my_pods[0],global_my_pods[1])
    pick_Behavior(global_my_pods[1],global_my_pods[0])

    global_turn += 1