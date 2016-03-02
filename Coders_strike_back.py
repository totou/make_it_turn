import sys
import math

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

    def is_last_checkpoint(self):
        return self.score == global_laps*len(global_checkpoints)-1

    def get_distance_checkpoint(self, checkpointId=None):
        if checkpointId is None:
            checkpointId = self.target
        return self.p.get_distance(global_checkpoints[checkpointId])

    def setRank(self, pods):
        self.rank=1
        for pod in pods:
            if pod != self :
                if pod.score>self.score:
                    self.rank+=1
                if pod.score == self.score and self.get_distance_checkpoint() > pod.get_distance_checkpoint():
                    self.rank+=1

    def get_num_tour_to_target(self, target=None):
        """Talking in speed only, not direction..."""
        if target is None:
            target=global_checkpoints[self.target]
        if self.v.get_norm() > 0:
            return int(self.p.get_distance(target) / self.v.get_norm())
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
            if self.get_angle_to_target(get_next_target(self.target)) < 45:
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
                    if Point(0,0).angleThreePoint(pod.v.to_Point(), self.v.to_Point()) < 25:
                        return False
                    print("Activate SHIELD", file=sys.stderr)
                    return True
        return False

    def get_angle_to_target(self, targeting=None):
        if targeting is None:
            targeting = global_checkpoints[self.target]
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

    def to_Point(self):
        return Point(self.x,self.y)

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

    def get_transposed_from_angle(self, angle_degre, dist_max=1):
        rad=math.radians(angle_degre)
        x=self.x+dist_max*math.cos(rad)
        y=self.y+dist_max*math.sin(rad)
        return Point(x,y)

    def angleThreePoint(self, point1, point2):
        do1=self.get_distance(point1)
        do2=self.get_distance(point2)
        d12=point1.get_distance(point2)
        if do1==0 or do2==0:
            return 0
        return math.degrees(math.acos((do1**2+do2**2-d12**2)/(2*do1*do2)))

    def angleThreePoint_signed(self,point1,point2):
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

def get_next_target(current_target_index):
    if current_target_index < len(global_checkpoints)-1:
        return global_checkpoints[current_target_index+1]
    else:
        return None

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




global_vmax = 1200
global_vattenuation = 0.85
global_max_rotation = 18
global_my_pods = [None, None]
global_ennemy_pods = [None, None]
global_checkpoints = []

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

    global_turn += 1