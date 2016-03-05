import sys, math

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
        self.bruiser_target = None
        self.bruiser_next_target = None

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
        if self.behaviour != "race":
            return self.bruiser_target
        return global_checkpoints[self.target_id]

    @property
    def next_target_id(self):
        if self.target_id < len(global_checkpoints)-1:
            return self.target_id + 1
        else:
            return 0

    @property
    def next_target(self):
        if self.behaviour != "race":
            return self.bruiser_next_target
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
            target = self.target
        if self.v.get_norm() > 0:
            return math.ceil(self.p.get_distance(self.target) / self.v.get_norm())
        else:
            return int(100)

    def will_reach_target_in_rounds(self, num_rounds, checkpoint_size=600, target=None):
        if target is None:
            target = self.target
        next_point = self.p
        for i in range(num_rounds):
            new_v = self.v * math.pow(global_vattenuation, i)
            next_point += new_v
            if target.get_distance(next_point) < checkpoint_size and new_v.get_norm() > 100:
                #print("Reaching target in {} turns".format(i+1), file=sys.stderr)
                return True, i+1
        return False, 0

    def calculate_new_thrust(self, num_rounds, checkpoint_size=600, attack_angle=0, reachable_in=None):
        max_speed = 200
        if global_turn == 0:
            return max_speed
        if self.activate_shield():
            return "SHIELD"
        if reachable_in is None and self.get_angle_to_target() > 45:
            return 0
        if reachable_in is not None:
            #print("Reaching target in {} turns".format(reachable_in), file=sys.stderr)
            if self.get_angle_to_target(self.next_target) < 45:
                #self.next_pod_for_destination(self.next_target, max_speed).will_reach_target_in_rounds(reachable_in-1, checkpoint_size):
                #print("Full thrust", file=sys.stderr)
                #return max_speed
                #print("Reduce thrust", file=sys.stderr)
                #check thrust to still pass in checkpoint
                pod_list_thrust = [[self.next_pod_for_destination(self.next_target, x), x] for x in range(max_speed,-1,-20)]
                # print('pod_list_thrust {}'.format(pod_list_thrust), file=sys.stderr)
                for pod_t, thrust in pod_list_thrust:
                    can_reach_t, _ = pod_t.will_reach_target_in_rounds(reachable_in-1, checkpoint_size)
                    #print('Reach {}, thrust {}'.format(can_reach_t,thrust), file=sys.stderr)
                    if can_reach_t:
                        next_angle_to_next_target = pod_t.get_angle_to_target(self.next_target)
                        if next_angle_to_next_target < 20 and pod_t.p.get_distance(self.next_target) > global_checkpoint_size*pod_t.v.get_norm():
                            return thrust
                        elif next_angle_to_next_target < 45:
                            return min(int(thrust * 5 / next_angle_to_next_target), thrust)
                #print('already going to checkpoint', file=sys.stderr)
            return 0
            #return int(max_speed * nb / 5)
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

        vx = self.vx + thrust*math.cos(math.radians(self.angle))
        vy = self.vy + thrust*math.sin(math.radians(self.angle))

        x = self.x + vx
        y = self.y + vy

        vx *= global_vattenuation
        vy *= global_vattenuation

        checkpoint_id = self.target_id
        score = self.score
        return Pod(x, y, vx, vy, angle, checkpoint_id, score)

    def get_angle_and_thrust_max(self, deep_max=3, angles=None, thrusts=None):
        """Return bool, angle, thrust, speed max"""
        if angles is None:
            angles = [-18, 0, 18]
        if thrusts is None:
            thrusts = [0, 100, 200]
        combinations = []
        for a in angles:
            for t in thrusts:
                combinations.append((a, t))
        res = {}
        if deep_max <= 0:
            for a, t in combinations:
                pod = self.next_pod_with_angle(a, t)
                res[(a, t)] = (pod.get_distance_checkpoint() < global_checkpoint_size, a, t, pod.v.get_norm_to_target(self.next_target))
        else:
            for a, t in combinations:
                new_angles = angles
                #if a < 0:
                #    new_angles = new_angles[:2]
                #if a > 0:
                #    new_angles = new_angles[1:]
                res[(a, t)] = self.next_pod_with_angle(a, t).get_angle_and_thrust_max(deep_max-1, angles=new_angles, thrusts=[th for th in thrusts if th >= t])
        feasible = False
        max_speed = 0
        res_angle = 0
        res_thrust = 0
        for c, r in res.items():
            if r[0]:
                feasible = True
                if max_speed <= r[3]:
                    max_speed = r[3]
                    res_angle = r[1]
                    res_thrust = r[2]
        return feasible, res_angle, res_thrust, max_speed

    def is_on_finish_line(self):
        return self.score == (len(global_checkpoints) * global_laps) - 1

    def calculate_new_direction_for_target(self, target=None, reachable_in=None):
        if target is None:
            target = self.target
        curr_vect = target - self.p
        #print("Direction to target is {}".format(curr_vect), file=sys.stderr)
        #print("Speed is {}".format(self.v), file=sys.stderr)
        #print("Reachable is {}".format(reachable_in), file=sys.stderr)
        if reachable_in is None:
            reachable_in = self.get_num_tour_to_target()
        for i in range(min(reachable_in, 10)):
            curr_vect -= self.v * math.pow(global_vattenuation, i)
        return curr_vect

    def next_position(self, n=1):
        return Point(self.p.x + self.v.x*global_vattenuation**(n-1), self.p.y + self.v.y*global_vattenuation**(n-1))

    def next_speed(self, n=1):
        return Vector(self.v.x*global_vattenuation**(n-1), self.v.y*global_vattenuation**(n-1))

    def activate_shield(self):
        if global_turn < 20:
            return False
        res = False
        for pod in global_ennemy_pods:
            if pod != self:
                #if pod.next_position().get_distance(self.next_position()) < 800:
                if self.is_impact_shield(pod):
                    #check speed to validate vmax ?
                    #if pod.v.get_norm()+self.v.get_norm() < global_vmax*0.2:
                    #    return False
                    #check angle
                    if Point(0, 0).angle_three_point(pod.v.to_Point(), self.v.to_Point()) < 25 and \
                            pod.v.get_norm() - self.v.get_norm() < global_vmax*0.3:
                        res = False
                    print("Activate SHIELD", file=sys.stderr)
                    return True
        if self.behaviour == "race":  # The first pod should also shield if collision with our other pod
            for pod in global_my_pods:
                if self != pod:
                    if pod.next_position().get_distance(self.next_position()) < 800 \
                            and pod.v.get_norm() > global_vmax*0.3:
                        return True
        return res

    def is_impact_shield(self, pod):
        step_number = 8
        #print("Starting points are {} {}".format(self.p, pod.p), file=sys.stderr)
        #print("Next positions are {} {}".format(self.next_position(), pod.next_position()), file=sys.stderr)
        step_vect_mine = (self.next_position()-self.p) * (1/step_number)
        step_vect_other = (pod.next_position()-pod.p) * (1/step_number)
        for i in range(1, step_number+1, 1):
            iter_point_self = (self.p + step_vect_mine*i).to_Point()
            iter_point_pod = (pod.p + step_vect_other*i).to_Point()
            #print("Points are {} {}".format(iter_point_self, iter_point_pod), file=sys.stderr)
            if iter_point_pod.get_distance(iter_point_self) < 800:
                #print("Impact detected", file=sys.stderr)
                return True
        return False

    def get_angle_to_target(self, targeting=None):
        if targeting is None:
            targeting = self.target
        new = self.p.get_transposed_from_angle(self.angle, 100)
        return self.p.angle_three_point(new, targeting)

    def set_behaviour(self, other, force_behaviour=None):
        if force_behaviour is not None:
            self.behaviour = force_behaviour
            return self.behaviour
        if self.score <= other.score - 1 and other.rank == 1:
            self.behaviour = "protect"
            return self.behaviour
        elif self.score <= other.score - 1 and other.rank == 1 and self.rank == 2:# If my 2 pods are first, run...
            self.behaviour = "race"
            return self.behaviour
        elif self.score <= other.score - 1 and other.rank > 1:
            self.behaviour = "bruiser"
            return self.behaviour
        elif self.score == other.score and other.rank > 1 and self.score >= 3:
            self.behaviour = "bruiser"
            return self.behaviour
        else:
            self.behaviour = "race"
            return self.behaviour

    def __str__(self):
        res = ''
        # res+="Point {0}\n".format(self.p)
        # res+="Vitesse {0}\n".format(self.v)
        # res+="Angle {0}\n".format(self.angle)
        # res+="Checkpoint {0}\n".format(self.target_id)
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

    def __pow__(self, other):
        return Vector(self.x ** other, self.y ** other)

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

    def __init__(self, x=None, y=None):
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
        res = (do1**2+do2**2-d12**2)/(2*do1*do2)
        if res > 1:
            res = 1
        if res < -1:
            res = -1
        return math.degrees(math.acos(res))

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


def get_next_target(current_target_index):
    if current_target_index < len(global_checkpoints)-1:
        return global_checkpoints[current_target_index+1]
    else:
        return None


def calculate_new_direction(pod, ignore_next=True):
    curr_target = pod.target
    next_target = pod.next_target
    curr_vect = curr_target - pod.p
    next_vect = next_target - pod.p
    #print("Target n is at {}".format(curr_vect.get_norm()), file=sys.stderr)
    #print("Target n+1 is at {}".format(next_vect.get_norm()), file=sys.stderr)
    curr_norm = curr_vect.get_norm()
    next_norm = next_vect.get_norm()
    speed = pod.calculate_new_thrust()
    if curr_norm > next_norm or ignore_next:
        # Target curr only
        #print("Target n only", file=sys.stderr)
        can_reach, number = pod.will_reach_target_in_rounds(global_will_reach_target)
        if not can_reach:
            new_target = pod.p.add_vector(curr_vect - pod.v * min(5, max(1, (pod.get_num_tour_to_target()-1))))
            print("{} {} {}".format(new_target.x, new_target.y, speed))
        else:
            print("{} {} {}".format(next_target.x, next_target.y, speed))
    else:
        # Combined vector
        #print("Target n and n+1", file=sys.stderr)
        ratio_norm = float(curr_norm / next_norm)
        my_ratio = int(5 * (1 / ratio_norm))
        new_target = pod.p.add_vector(my_ratio*curr_vect + next_vect)
        print("{} {} {}".format(new_target.x, new_target.y, speed))
        if not pod.will_reach_target_in_rounds(global_will_reach_target):
            new_target = pod.p.add_vector(curr_vect - pod.v * max(1, (pod.get_num_tour_to_target()-1)))
            print("{} {} {}".format(new_target.x, new_target.y, speed))
        else:
            print("{} {} {}".format(next_target.x, next_target.y, speed))


def calculate_new_direction_new_method(pod, ignore_next=True):
    nb_turns_to_next_target = pod.turn_needed_to_orientate_to_next_checkpoint()
    can_reach, nb = pod.will_reach_target_in_rounds(nb_turns_to_next_target, global_checkpoint_size)# At least check 5 rounds in advance
    #print("Can reach point {} in {} turns".format(can_reach, nb), file=sys.stderr)
    if not can_reach:
        thrust = pod.calculate_new_thrust(nb_turns_to_next_target, global_checkpoint_size)
        curr_vect = pod.calculate_new_direction_for_target()
        new_target = pod.p.add_vector(curr_vect)
        #curr_vect = pod.target - pod.p
        #new_target = pod.p.add_vector(curr_vect - pod.v * max(1, (pod.get_num_tour_to_target()-1)))
        print("{} {} {}".format(int(new_target.x), int(new_target.y), thrust))
    else:
        max_deep = 4
        if nb <= max_deep and False:
            reachable, angle_to_follow, thrust, speed = pod.get_angle_and_thrust_max(deep_max=nb)
        else:
            reachable = False
        if reachable:
            # New technique
            print("Reachable {} {} {}".format(angle_to_follow, thrust, speed), file=sys.stderr)
            # Deduce a point from the angle
            new_target = pod.p.get_transposed_from_angle(angle_to_follow, dist_max=1000)
            print("{} {} {}".format(int(new_target.x), int(new_target.y), thrust))
        else:
            # Like old times
            thrust = pod.calculate_new_thrust(nb_turns_to_next_target, global_checkpoint_size, reachable_in=nb)
            curr_vect = pod.calculate_new_direction_for_target(pod.next_target, reachable_in=nb)
            new_target = pod.p.add_vector(curr_vect)
            print("{} {} {}".format(int(new_target.x), int(new_target.y), thrust))


def get_first_ennemy():
    if global_ennemy_pods[0].rank < global_ennemy_pods[1].rank:
        return global_ennemy_pods[0]
    else:
        return global_ennemy_pods[1]

def get_my_bruiser():
    if global_my_pods[0].behaviour != "race":
        return global_my_pods[0]
    if global_my_pods[1].behaviour != "race":
        return global_my_pods[1]
    return None

def can_bruise_well(my_bruiser, target_ennemy):
    if target_ennemy.target.get_distance(my_bruiser.p) < target_ennemy.target.get_distance(target_ennemy.p):
        return True
    return False

def define_bruiser_targets():
    my_bruiser = get_my_bruiser()
    target_ennemy = get_first_ennemy()
    if my_bruiser is None:
        return
    if can_bruise_well(my_bruiser, target_ennemy):
        my_bruiser.bruiser_target = target_ennemy.next_position()
        my_bruiser.bruiser_next_target = my_bruiser.bruiser_target
    else:
        # Prepare: go to checkpoint
        my_bruiser.bruiser_target = target_ennemy.next_target
        my_bruiser.bruiser_next_target = target_ennemy.p
    #print("Bruisers targets: {} {}".format(my_bruiser.bruiser_target, my_bruiser.bruiser_next_target), file=sys.stderr)


global_vmax = 1200
global_vattenuation = 0.85
global_checkpoint_size = 600
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
    # Set behaviours
    global_my_pods[0].set_behaviour(global_my_pods[1])
    global_my_pods[1].set_behaviour(global_my_pods[0])
    define_bruiser_targets()

    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    for my_pod in global_my_pods:
        calculate_new_direction_new_method(my_pod)
        # print("8000 4500 100")
        # print("8000 4500 100")

    global_turn += 1
