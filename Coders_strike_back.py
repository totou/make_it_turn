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
        #for 1 to 4 depending on position
        self.rank = 0
        self.state = 'runner'

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
            return math.ceil(self.p.get_distance(target) / self.v.get_norm())
        else:
            return 100

    def will_reach_target_in_rounds(self, num_rounds,checkpoint_size,target):
        if target is None:
            target = global_checkpoints[self.target]
        speed = self.v
        next_point = self.p
        for i in range(num_rounds):
            next_point += speed * math.pow(global_vattenuation, i)
            if target.get_distance(next_point) < checkpoint_size:
                return (True, i+1)
        return (False, 0)

    def calculate_new_thrust(self,num_rounds, checkpoint_size, attack_angle, target=None, next_target=None):
        if target is None:
            target=global_checkpoints[self.target]
        if next_target is None:
            next_target = global_checkpoints[get_next_target_id(self.target)]
        max_speed = 200
        if global_turn==0:
            return max_speed
        if self.activate_shield():
            return "SHIELD"
        can_reach, nb = self.will_reach_target_in_rounds(num_rounds,checkpoint_size, target)
        if can_reach and nb < num_rounds:
            if self.get_angle_to_target(target) > attack_angle:
                print('Angle too big do not thust: {}'.format(self.get_angle_to_target(target)), file=sys.stderr)
                return 0
            if self.is_last_checkpoint():
                print('last sprint', file=sys.stderr)
                return max_speed
            #someone in the way -> CHAAAARGE
            # for i in range(nb):
            #     my_pos = self.next_position(i)
            #     for pod in global_my_pods+global_ennemy_pods:
            #         if pod != self:
            #             if pod.next_position(i).get_distance(my_pos) < 800:
            #                 print('CHARGE', file=sys.stderr)
            #                 return max_speed
            # #check thrust to still pass in checkpoint
            pod_list_thrust=[[self.next_pod(next_target,x),x]  for x in range(max_speed,-1,-20)]
            # print('pod_list_thrust {}'.format(pod_list_thrust), file=sys.stderr)
            for pod_t, thrust in pod_list_thrust:
                can_reach_t, _ = pod_t.will_reach_target_in_rounds(num_rounds-1,checkpoint_size,target)
                # print('Reach {}, thrust {}'.format(can_reach_t,thrust), file=sys.stderr)
                if can_reach_t and pod_t.get_angle_to_target(next_target) < 20 :
                    print('I can reach', file=sys.stderr)
                    return thrust
            print('already going to checkpoint', file=sys.stderr)
            return 0
            #return int(max_speed * nb / 5)
        print('When in doubt', file=sys.stderr)
        return 200

    def next_pod(self,destination,thrust):
        #first find angle
        cur_proj = self.p.get_transposed_from_angle(self.angle,10)
        next_proj = destination
        rotation = self.p.angleThreePoint_signed(cur_proj,next_proj)
        if rotation > global_max_rotation:
            rotation = global_max_rotation
        if rotation < -global_max_rotation:
            rotation = -global_max_rotation
        angle = self.angle+rotation

        vx=self.vx+thrust*math.cos(math.radians(self.angle))
        vy=self.vy+thrust*math.sin(math.radians(self.angle))

        x=self.x+vx
        y=self.y+vy

        vx*=global_vattenuation
        vy*=global_vattenuation

        checkpointId=self.target
        score=self.score
        return Pod(x, y, vx, vy, angle, checkpointId, score)

    def next_position(self, n=1):
        speed=self.v
        n_speed=Vector(0,0)
        for i in range(n):
            n_speed += speed* global_vattenuation**(i)
        return Point(self.p.x + n_speed.x, self.p.y + n_speed.y)

    def activate_shield(self):
        for pod in global_my_pods+global_ennemy_pods:
            if pod != self:
                if pod.next_position().get_distance(self.next_position()) < 800:
                    if self.state == 'runner':
                        #check speed to validate vmax ?
                        print('Norm {}'.format(pod.v.get_norm()+self.v.get_norm()), file=sys.stderr)
                        if pod.v.get_norm()+self.v.get_norm() < global_vmax*0.3:
                            return False
                        # #check angle
                        print('angle {}'.format(Point(0,0).angleThreePoint(pod.v.to_Point(), self.v.to_Point())), file=sys.stderr)
                        if Point(0,0).angleThreePoint(pod.v.to_Point(), self.v.to_Point()) < 45 :
                            print('distance {}'.format(self.get_distance_checkpoint()), file=sys.stderr)
                            if self.get_distance_checkpoint() > pod.v.get_norm()+self.v.get_norm()*5:
                                return False

                    if self.state=='bruiser' and pod in global_my_pods:
                        return False

                    print("Activate SHIELD", file=sys.stderr)
                    return True
        return False

    def get_angle_to_target(self, targeting):
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

    def to_Point(self):
        return Point(self.x,self.y)

class Point(object):

    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

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


def get_first_pod():
    for pod in global_my_pods+global_ennemy_pods:
        if pod.rank == 1:
            return pod


standard_runner={'checkpoint_size':550, 'turn_to_turn':5, 'angle_to_speed':45}
agressive_runner={'checkpoint_size':550, 'turn_to_turn':5, 'angle_to_speed':45}
# agressive_runner={'checkpoint_size':600, 'turn_to_turn':4, 'angle_to_speed':45}

def runner(pod):
    print("I am a runner", file=sys.stderr)
    behavior_dict=standard_runner

    curr_target = global_checkpoints[pod.target]
    next_target = global_checkpoints[get_next_target_id(pod.target)]
    checkpoint_size = behavior_dict['checkpoint_size']
    angle_to_speed = curr_target.angleThreePoint(pod.p,next_target)
    num_turn = max(1,math.ceil((180-angle_to_speed)/global_max_rotation))
    curr_vect = curr_target - pod.p
    next_vect = next_target - pod.p
    print("angle_to_speed {}".format(angle_to_speed), file=sys.stderr)
    print("num_turn {}".format(num_turn), file=sys.stderr)
    #print("Target n+1 is at {}".format(next_vect.get_norm()), file=sys.stderr)
    curr_norm = curr_vect.get_norm()
    next_norm = next_vect.get_norm()
    speed = pod.calculate_new_thrust(num_turn, checkpoint_size, angle_to_speed)
    can_reach, number = pod.will_reach_target_in_rounds(num_turn, checkpoint_size,curr_target)
    if not can_reach or pod.is_last_checkpoint():
        print("num_turn nr {}".format(min(num_turn,max(1,(pod.get_num_tour_to_target())))), file=sys.stderr)
        n_speed=Vector(0,0)
        for i in range(min(num_turn,max(1,(pod.get_num_tour_to_target())))):
            n_speed += pod.v* global_vattenuation **(i)
        new_target = pod.p.add_vector(curr_vect - n_speed )
        if pod.p.angleThreePoint(new_target,pod.p.get_transposed_from_angle(pod.angle,10)) > 60:
            speed = 0
        print("{} {} {}".format(int(new_target.x), int(new_target.y), speed))
    else:
        print("num_turn r {}".format(max(1,(pod.get_num_tour_to_target(next_target)))), file=sys.stderr)
        n_speed=Vector(0,0)
        for i in range(max(1,(pod.get_num_tour_to_target(next_target)))):
            n_speed += pod.v* global_vattenuation **(i)
        new_target = pod.p.add_vector(next_vect - n_speed )
        print("{} {} {}".format(int(new_target.x), int(new_target.y), speed))


global_bruiser_state = 'defense'
def bruiser(pod):
    global global_bruiser_state
    pod.state='bruiser'
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
    print("Bruiser state {}".format(global_bruiser_state), file=sys.stderr)
    if global_bruiser_state=='attack' or pod_target.is_last_checkpoint():
        print("Bruiser on target", file=sys.stderr)
        speed=0
        n=0
        if pod_target.v.get_norm()!=0:
            n=math.ceil(pod.p.get_distance(pod_target.p)/(pod_target.v.get_norm()+pod.v.get_norm()))
        extrapolate_target = pod_target.next_position(n)
        if pod.activate_shield():
            speed = 'SHIELD'
        elif pod.p.get_distance(pod_target.p) <  4000:
            speed = 200
        n_speed=Vector(0,0)
        for i in range(n):
            n_speed += pod.v * global_vattenuation **(i)
        curr_vect = extrapolate_target - pod.p
        new_target = pod.p.add_vector(curr_vect - n_speed)
        print("{} {} {}".format(new_target.x, new_target.y, speed))
    else:
        # go and stop on checkpoint
        behavior_dict=standard_runner
        next_target = pod_target
        checkpoint_size = behavior_dict['checkpoint_size']
        angle_to_speed = curr_target.angleThreePoint(pod.p,next_target)
        num_turn = max(1,math.ceil((180-angle_to_speed)/global_max_rotation))
        curr_vect = curr_target - pod.p
        next_vect = next_target - pod.p
        print("angle_to_speed {}".format(angle_to_speed), file=sys.stderr)
        print("num_turn {}".format(num_turn), file=sys.stderr)
        #print("Target n+1 is at {}".format(next_vect.get_norm()), file=sys.stderr)
        speed = pod.calculate_new_thrust(num_turn, checkpoint_size, angle_to_speed, target=curr_target,next_target=next_target)
        can_reach, number = pod.will_reach_target_in_rounds(num_turn, checkpoint_size,curr_target)
        if not can_reach:
            print("num_turn nr {}".format(min(num_turn,max(1,(pod.get_num_tour_to_target(curr_target))))), file=sys.stderr)
            n_speed=Vector(0,0)
            for i in range(min(num_turn,max(1,(pod.get_num_tour_to_target(curr_target))))):
                n_speed += pod.v* global_vattenuation **(i)
            new_target = pod.p.add_vector(curr_vect - n_speed )
            if pod.p.angleThreePoint(new_target,pod.p.get_transposed_from_angle(pod.angle,10)) > 60:
                speed = 0
            print("{} {} {}".format(int(new_target.x), int(new_target.y), speed))
        else:
            print("num_turn r {}".format(max(1,(pod.get_num_tour_to_target(next_target)))), file=sys.stderr)
            n_speed=Vector(0,0)
            for i in range(max(1,(pod.get_num_tour_to_target(next_target)))):
                n_speed += pod.v* global_vattenuation **(i)
            new_target = pod.p.add_vector(next_vect - n_speed )
            print("{} {} {}".format(int(new_target.x), int(new_target.y), speed))

global_bruiser_state = 'position'
def helper(pod):
    pod_partner = [x for x in global_my_pods if x != pod][0]



def pick_Behavior(pod,friend):
    if pod.score<1:
        runner(pod)
    elif pod.rank==1:
        runner(pod)
    elif pod.rank==2:
        runner(pod)
    elif pod.rank < friend.rank:
        runner(pod)
    # elif pod.rank == 2:
    #     #agressive
    #     runner(pod,agressive=agressive)
    # elif pod.score > get_first_pod().score -2:
    #     # (very ?) agressive
    #     runner(pod,agressive=agressive)
    else:
        bruiser(pod)
        # runner(pod)

global_vmax = 1200
global_vattenuation = 0.85
global_max_rotation = 18
global_my_pods = [None, None]
global_ennemy_pods = [None, None]
global_checkpoints = []

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
            if nextCheckPointId != global_my_pods[i].target:
                global_my_pods[i].score += 1
            global_my_pods[i] = Pod(x, y, vx, vy, angle, nextCheckPointId, score=global_my_pods[i].score)
    for i in range(2):
        x, y, vx, vy, angle, next_check_point_id = [int(j) for j in input().split()]
        if global_turn == 0:
            global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id)
        else:
            if next_check_point_id != global_ennemy_pods[i].target:
                global_ennemy_pods[i].score += 1
            global_ennemy_pods[i] = Pod(x, y, vx, vy, angle, next_check_point_id, score=global_ennemy_pods[i].score)

    all_pod=global_my_pods+global_ennemy_pods
    for pod in all_pod:
        pod.setRank(all_pod)
        # print(pod, file=sys.stderr)
        # print(solver_x2(pod.p,global_checkpoints[pod.target],global_checkpoints[get_next_target_id(pod.target)]), file=sys.stderr)

    # To debug: print("Debug messages...", file=sys.stderr)

    pick_Behavior(global_my_pods[0],global_my_pods[1])
    pick_Behavior(global_my_pods[1],global_my_pods[0])

    global_turn += 1