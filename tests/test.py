from panda_collisions import panda_collisions
from panda3d.core import LVector3f, LPoint3f
import unittest
from vector import vector

class Wrapper:
    def __init__(self):

        self.b = None
        self.collisions = panda_collisions.CollisionWrapper()
        
        self.single_update = False

class MyCollisionTest(unittest.TestCase):
    
    def test_simple(self):
        
        W = Wrapper()
        
        # this is just printing the collision dict froma  previous run of the same function
        # and copy pasting it here.
        
        expected_output = {'myNPC2': {'myNPC1': {'from tag': 'NPC', 'from id': 'myNPC2', 'into tag': 'NPC', 'into id': 'myNPC1', 'collision normal': LVector3f(1, 0, 0), 'interior point': LPoint3f(-0.2, 0, 0), 'surface point': LPoint3f(0.3, 0, 0)}}, 'myNPC1': {'myNPC2': {'from tag': 'NPC', 'from id': 'myNPC1', 'into tag': 'NPC', 'into id': 'myNPC2', 'collision normal': LVector3f(-1, 0, 0), 'interior point': LPoint3f(0.3, 0, 0), 'surface point': LPoint3f(-0.2, 0, 0)}}}
        
        W.collisions.update(
            {"create": {"myNPC1": "NPC", "myNPC2": "NPC", "myNPC3": "NPC"}})
        W.collisions.update({"update": {
            # setting position and rotation
            "myNPC1": ((0, 0, 0), (0, 0, 0)),
            "myNPC2": ((0.1, 0, 0), (0, 0, 0)),
            "myNPC3": ((5, 0, 0), (0, 0, 0))}})

        W.single_update = True
        
        collisions = W.collisions.collision_checks()
        
        # because of floating point precision BS, the regular
        # assert expected_output == collisions
        # will fail.
        # so we have to create an in depth crawler that checks values
        # one by one and if there is a mismatch, rounds to a decimal
        # where it's and the values *ARE* "Equal"
        match = recursive_unequal(collisions,expected_output)
        assert match

def recursive_unequal(my_dict,compare_dict):
    all_equal=True
    for key in my_dict:
        if type(my_dict[key])==dict:
            recursive_unequal(my_dict[key],compare_dict[key])
        else:
            eq = my_dict[key] == compare_dict[key]
            if not eq:
                nv1 = vector.Vector(*my_dict[key])
                nv2 = vector.Vector(*compare_dict[key])
                nv1 = round(nv1,5)
                nv2 = round(nv2,5)
                eq = nv1 == nv2
            if not eq:
                all_equal = False
    return all_equal

if __name__ == "__main__":
    unittest.main()
