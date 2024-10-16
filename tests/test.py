from panda_collisions import panda_collisions
from panda3d.core import LVector3f, LPoint3f
import unittest
from vector import vector

class Wrapper:
    def __init__(self):

        self.b = None
        self.collisions = panda_collisions.CollisionWrapper()
        
        self.single_update = False

class WorldObject:
    def __init__(self,myid):
        self.id = myid
        self.verts = []
        self.faces = [[0,1,2,3]] # this has to be a list of lists, with
        # one entry. best don't change this if you don't want to 
        # dig into how object creation works.

class MyCollisionTest(unittest.TestCase):
    
    def test_simple(self):
        
        W = Wrapper()
        
        # this is just printing the collision dict froma  previous run of the same function
        # and copy pasting it here.
        
        expected_output = {'myNPC2': {'myNPC1': {'from tag': 'NPC', 'from id': 'myNPC2', 'into tag': 'NPC', 'into id': 'myNPC1', 'collision normal': LVector3f(1, 0, 0), 'interior point': LPoint3f(-0.2, 0, 0), 'surface point': LPoint3f(0.3, 0, 0), 'from part id': None, 'into part id': None}}, 'myNPC1': {'myNPC2': {'from tag': 'NPC', 'from id': 'myNPC1', 'into tag': 'NPC', 'into id': 'myNPC2', 'collision normal': LVector3f(-1, 0, 0), 'interior point': LPoint3f(0.3, 0, 0), 'surface point': LPoint3f(-0.2, 0, 0), 'from part id': None, 'into part id': None}}}

        
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
    
    def test_basic_terrain_setup(self):
        W = Wrapper()
        
        terrain_ob = WorldObject("terrain_id")
        terrain_ob.pos=(0,0,0)
        terrain_ob.verts = [(0,0,0),(2,0,0),(2,2,0),(0,2,0)]
        #World.py:10184: specialdict.mysetter(self.collision_inputs,["create complex",myuiob.id],(myuiob,"UI")) # "create, id, tagname
        W.collisions.update({
            "create": {"myNPC1": "NPC"}, 
            "create complex":{"terrain_id":(terrain_ob,"terrain")},
            "create subpart":{"myNPC1":{
                    "sub part id":"groundray",
                    "sub tagname":"terrainray",
                    "sub part shape":("ray",None), # could be ("name",direction vector = (0,0,-1)) but none is default
                    "sub part offset":(0,0,5),
                    "sub part rotation":(0,0,0),
                    }},
                })
            
        W.collisions.update({"update": {"myNPC1": ((1, 1, 0), (0, 0, 0))}})
        r = W.collisions.collision_checks()
        
        # basic setup works
        assert r == {'myNPC1': {'terrain_id': {'from tag': 'terrainray', 'from id': 'myNPC1', 'into tag': 'terrain', 'into id': 'terrain_id', 'collision normal': LVector3f(0, 0, 1), 'interior point': LPoint3f(1, 1, 0), 'surface point': LPoint3f(1, 1, 0), 'from part id': 'groundray', 'into part id': None}}}

        
        
        # updating position works, and returns correct follow up points
        W.collisions.update({"update": {"myNPC1": ((1.1, 1.1, 0), (0, 0, 0))}})
        r = W.collisions.collision_checks()
        
        assert r == {'myNPC1': {'terrain_id': {'from tag': 'terrainray', 'from id': 'myNPC1', 'into tag': 'terrain', 'into id': 'terrain_id', 'collision normal': LVector3f(0, 0, 1), 'interior point': LPoint3f(1.1, 1.1, 0), 'surface point': LPoint3f(1.1, 1.1, 0), 'from part id': 'groundray', 'into part id': None}}}

        
        
        # I guess I should add a test for cleanup?
        
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
