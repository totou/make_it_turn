class Pod(object):
    def __init__(self, x, y, vx, vy, angle, targetCheckpoint, score=0):
        self._x = x
        self._y = y
        self.p = Point(x, y)
        self.vx = vx
        self.vy = vy
        self.v = Vector(vx, vy)
        self.angle = angle
        self.target = targetCheckpoint
        self.score = score

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

    def get_num_tour_to_target(self):
        """Talking in speed only, not direction..."""
        if self.v.get_norm() > 0:
            return int(self.p.get_distance(global_checkpoints[self.target]) / self.v.get_norm())
        else:
            return int(100)

    def will_reach_target_in_rounds(self, num_rounds=5):
        dist_to_destination = self.p.get_distance(global_checkpoints[self.target])
        speed = self.v.get_norm()
        next_point = self.p
        for i in range(num_rounds):
            next_point += self.v * math.pow(0.8, i)
            if global_checkpoints[self.target].get_distance(next_point) < 600:
                return (True, i+1)
        return (False, 0)

    def calculate_new_thrust(self):
        if self.activate_shield():
            return "SHIELD"
        if self.get_angle_to_target() > 45:
            return 0
        max_speed = 200
        can_reach, nb = self.will_reach_target_in_rounds(5)
        if can_reach and nb <= 5:
            if self.get_angle_to_target(get_next_target_id(self.target)) < 45:
                return max_speed
            return 0
            #return int(max_speed * nb / 5)
        return max_speed

    def is_on_finish_line(self):
        return self.score == (len(global_checkpoints) * global_laps) - 1

    def calculate_new_direction_for_curr_target(self):
        curr_target = global_checkpoints[self.target]
        curr_vect = curr_target - self.p
        if self.is_on_finish_line():
            print("FINISH HIM", file=sys.stderr)
            return curr_vect
        _, nb = self.will_reach_target_in_rounds(5)
        if nb == 0:
            nb = self.get_num_tour_to_target()
        return curr_vect - self.v * nb

    def next_position(self):
        return Point(self.p.x + self.v.x, self.p.y + self.v.y)

    def activate_shield(self):
        for epod in global_ennemy_pods:
            if epod.next_position().get_distance(self.next_position()) < 800:
                print("Activate SHIELD", file=sys.stderr)
                return True
        return False

    def get_angle_to_target(self, targeting=None):
        if targeting is None:
            targeting = self.target
        new = self.p.get_transposed_from_angle(self.angle)
        return self.p.angleThreePoint(new, global_checkpoints[targeting])


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

    def get_transposed_from_angle(self, angle_degre, dist_max=1):
        rad=math.radians(angle_degre)
        x=self.x+dist_max*math.cos(rad)
        y=self.y+dist_max*math.sin(rad)
        return Point(x,y)

    def angleThreePoint(self,point1,point2):
        do1=self.get_distance(point1)
        do2=self.get_distance(point2)
        d12=point1.get_distance(point2)
        if do1==0 or do2==0:
            return 0
        return math.degrees(math.acos((do1**2+do2**2-d12**2)/(2*do1*do2)))


    def get_circle(self, dist_max, division=400):
        res = []
        for x in xrange(self.x - dist_max, self.x + dist_max, division):
            res.append(Point(x, self.y - dist_max))
        for x in xrange(self.x - dist_max, self.x + dist_max, division):
            res.append(Point(x, self.y + dist_max))
        for y in xrange(self.y - dist_max, self.y + dist_max, division):
            res.append(Point(self.x - dist_max, y))
        for y in xrange(self.y - dist_max, self.y + dist_max, division):
            res.append(Point(self.x + dist_max, y))
        return list(set([self.get_transposed_from_point(p, dist_max) for p in res]))

def get_next_target_id(current_target_index):
    if current_target_index < len(global_checkpoints)-1:
        return current_target_index+1
    else:
        return 0


def calculate_new_direction(pod, ignore_next=True):
    curr_target = global_checkpoints[pod.target]
    next_target = global_checkpoints[get_next_target_id(pod.target)]
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
        can_reach, number = pod.will_reach_target_in_rounds(5)
        if not can_reach:
            new_target = pod.p.add_vector(curr_vect - pod.v * min(5,max(1,(pod.get_num_tour_to_target()-1))) )
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
        if not pod.will_reach_target_in_rounds(5):
            new_target = pod.p.add_vector(curr_vect - pod.v * max(1,(pod.get_num_tour_to_target()-1)))
            print("{} {} {}".format(new_target.x, new_target.y, speed))
        else:
            print("{} {} {}".format(next_target.x, next_target.y, speed))




global_my_pods = [None, None]
global_ennemy_pods = [None, None]
global_checkpoints = []

import sys
import math

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
while True:
    for i in range(2):
        x, y, vx, vy, angle, nextCheckPointId = [int(j) for j in input().split()]
        if global_my_pods[i] is not None and nextCheckPointId != global_my_pods[i].target:
            global_my_pods[i] = Pod(x, y, vx, vy, angle, nextCheckPointId, score=global_my_pods[i].score + 1)
        elif global_my_pods[i] is not None:
            global_my_pods[i] = Pod(x, y, vx, vy, angle, nextCheckPointId, score=global_my_pods[i].score)
        else:
            global_my_pods[i] = Pod(x, y, vx, vy, angle, nextCheckPointId)
    for i in range(2):
        x, y, vx, vy, angle, next_check_point_id = [int(j) for j in input().split()]
        #global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id)
        if global_ennemy_pods[i] is not None and next_check_point_id != global_ennemy_pods[i].target:
            global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id, score=global_ennemy_pods[i].score + 1)
        elif global_ennemy_pods[i] is not None:
            global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id, score=global_ennemy_pods[i].score)
        else:
            global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id)


    # Write an action using print
    # To debug: print("Debug messages...", file=sys.stderr)

    for mypod in global_my_pods:
        calculate_new_direction(mypod)
        # print("8000 4500 100")
        # print("8000 4500 100")

