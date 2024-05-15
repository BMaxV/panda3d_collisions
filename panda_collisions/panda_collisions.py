#for collisions
from panda3d.core import CollisionTraverser
from panda3d.core import CollisionNode
from panda3d.core import CollisionHandlerQueue
from panda3d.core import CollisionHandlerPusher
from panda3d.core import CollisionRay
from panda3d.core import CollisionSphere
from panda3d.core import BitMask32

from panda3d.core import NodePath

from panda_object_create import panda_object_create_load

# Ok, crash course. This topic is a bit complicated, and may take multiple tries to get.

# highly recommend reading the manual if you're reading comments
# https://docs.panda3d.org/1.10/python/programming/collision-detection/index
# yes, do it again. Mind the version I'm linking here.

# You want a collision between two objects.

# fundamentally, the process goes like this:
    
    # ObjectA.setup()
    # ObjectB.setup()
    # collisiontraverser.traverse()
    # your_collision = collisionhandlerqueue.getentries()
    
# Done.

# Now for the details. E.g. "how to set up mouse click.

# step 1
# setup_mouse_click creates our "ObjectA" the ray that is being cast
# from the camera, into the scene.

# step 2
# create_collision_node creates our "ObjectB" a sphere with radius 0.3

# step 3
# actually check for the collision with mouse_ray_check


# Bonus step: Bitmasks 

# pandas collision system is pretty clever.
# some parts you WANT to check for collision, like [ray -> enemy] or [ray -> object]
# and some parts you DONT want to check for collision, like [ray -> grass in front of enemy]

# so panda has bit masks.
# if two bitmasks OVERLAP, a collision CAN happen
# if they don't, a collision CANT happen

# e.g.  
# "mouseray":"from":BitMask32(0b0111)
# or 111
# "item":"into":BitMask32(0b0100)
# or 100

# because the first bit overlaps, the mouse ray can collide with the item!

# compared to:
# "waypoint": "from":BitMask32(0b0000),
# "NPC": "into":BitMask32(0b0011)},

# because 000 and 011 DONT overlap, a collision can NEVER happen

# ---

# but because 
# 111 from the mouse ray and "waypoint":"into":BitMask32(0b0100)
# AND
# 111 from the mouse ray and "NPC":"into":BitMask32(0b0011)},
# BOTH overlap, but in different places,
# the mouse ray will collide with both and you can click on both.

class CollisionWrapper:
    def __init__(self,client=True,simple_collision_radius=0.3):        
        self.node_root = NodePath("node_root")
        self.simple_collision_radius = simple_collision_radius
        self.collision_objects = {}
        self.collision_bins = {}
        
        # see the bitmask step at the beginning for what this means.
        self.bitmasks={"mouseray":
            {"from":BitMask32(0b0111),"into":BitMask32(0b0000)},
                        "terrain":
            {"from":BitMask32(0b0000),"into":BitMask32(0b0100)},
                        "waypoint": 
            {"from":BitMask32(0b0000),"into":BitMask32(0b0100)},
                        "UI": 
            {"from":BitMask32(0b0000),"into":BitMask32(0b0100)},
                        "item":
            {"from":BitMask32(0b0000),"into":BitMask32(0b0100)},
                        "players":
            {"from":BitMask32(0b0001),"into":BitMask32(0b0011)},
                        "NPC":
            {"from":BitMask32(0b0001),"into":BitMask32(0b0011)},
                        "projectile":
            {"from":BitMask32(0b0001),"into":BitMask32(0b0011)},
                        "wall":
            {"from":BitMask32(0b0001),"into":BitMask32(0b0011)},
            }
        
        
        self.cTrav = CollisionTraverser()
        self.client_mouse_hover = client
        
        if client:
            self.setup_mouse_ray()
        pusher = False
        if pusher:
        #alternative collisions handlers?
            self.CH_world = CollisionHandlerPusher() #which means this should be filled
        else:
            self.CH_world = CollisionHandlerQueue()
    
    def create_new_bin(self,name):
        P=NodePath(name)
        P.reparentTo(self.node_root)
        self.collision_bins[name]=P
    
    def update(self,input_d):
        """
        The input has to be structured as
        
        this will require a dictionary as input
        
        {"create":
            {ob_id:"tag_name",
            ...},
         "update":
            {ob_id:position, # as 3 value tuple or something
            ...},
        }
        """
        # tags I want... Actors, terrain, UI, Walls/structures?
        # then check the queue for the collisions I have found.
        
        if "create" in input_d:
            for ob_id in input_d["create"]:
                
                tag_name = input_d["create"][ob_id]
                self.create_collision_node(ob_id,tag_name)
        
        if "create complex" in input_d:
            # ok, doing this, having objects be keys in an input
            # dict is incredibly annoying, I should not be doing this.
            for wo_id in input_d["create complex"]:
                wo = input_d["create complex"][wo_id][0]
                tagname = input_d["create complex"][wo_id][1]
                self.create_complex(wo,tagname=tagname)
        
        if "update" in input_d:
            for ob_id in input_d["update"]:
                if ob_id not in self.collision_objects:
                    continue
                
                data = input_d["update"][ob_id]
                
                self.collision_objects[ob_id].setPos(*tuple(data[0]))
                
                if data[1] != None:
                    self.collision_objects[ob_id].setHpr(*tuple(data[1]))
        
                
        if "bin move" in input_d:
            
            for ob_id, new_bin in input_d["bin move"]:
                if new_bin not in self.collision_bins:
                    self.create_new_bin(new_bin)
                my_bin=self.collision_bins[new_bin]
                self.collision_objects[ob_id].reparent_to(my_bin)
        
        if "destroy" in input_d:
            for ob_id in input_d["destroy"]:
                if ob_id not in self.collision_objects:
                    continue
                ob=self.collision_objects[ob_id]
                ob.removeNode()
                self.collision_objects.pop(ob_id)
            input_d["destroy"]=[]
    
    def create_complex(self,world_object,tagname="terrain"):
        """ 
        this depends on my custom object function, which is kind
        of optional, so...
        
        let's comment that out or move it to a different file?
        """
        
        collision_mask = self.bitmasks[tagname]["into"]
        my_ob = panda_object_create_load.make_object(self.node_root,world_object.verts,world_object.faces,tag_tuple=(tagname,str(world_object.id)),collision_mask=collision_mask)
        self.collision_objects[world_object.id] = my_ob
        my_ob.setPos(*world_object.pos)
    
    def clear_all(self):
        for key in self.collision_objects:
            ob=self.collision_objects[key]
            ob.removeNode()
        
        self.collision_objects={}
    
    def collision_checks(self):
        #actually look for collisions
        
        # node root is the root of a tree
        # root
        # - bin
        #   - object1
        #   - object2
        # - bin 2
        #   - object3
        #   - object4
        
        self.cTrav.traverse(self.node_root)
        collision_d = self.get_ids_from_collisions()
        return collision_d
        
        if False:
                if type(world_ob).__name__=="ContainerProjectile":
                    
                    tag_tuple=("projectile",str(world_ob.id))
                    collision_mask=BitMask32.bit(1)
                    self.attach_collision_node(engine_ob,tag_tuple)
         
    def create_collision_node(self,ob_id,tag_name,radius=None):
        """
        ob_id and tagname are arbitray, but should be basic types that can be used as
        dictionary keys.
        
        step 2 for the crash course
        """
        
        if radius == None:
            radius = self.simple_collision_radius
        
        # same pattern as the mouse ray
        # define node type and shape
        col_Node = CollisionNode("general_col_node")
        col_body = CollisionSphere((0,0,0),radius)
        col_Node.addSolid(col_body)
        
        # track the object.
        col_NodeNP = NodePath(col_Node)
        col_NodeNP.reparentTo(self.node_root)
        
        # tag is being used to recover the object
        col_NodeNP.set_tag(tag_name,str(ob_id))
        
        # add it to another datastructure to track it via id.
        self.collision_objects[ob_id] = col_NodeNP
        
        # set mask
        # masks handle WHICH collisions are being looked for
        # see __init__
        col_Node.setFromCollideMask(self.bitmasks[tag_name]["from"])
        col_Node.setIntoCollideMask(self.bitmasks[tag_name]["into"])
        
        #set it up so it's being tracked.
        self.cTrav.addCollider(col_NodeNP,self.CH_world)
        
    def fetch_objects_from_collision(self,collisionargs):
        #I should unpack these.
        """
        https://docs.panda3d.org/1.10/python/reference/panda3d.core.CollisionEntry#panda3d.core.CollisionEntry
        """
        #print("panda collisions, collisionargs\n", collisionargs[0])
        #print(collisionargs[0])
        fromn = collisionargs[0].from_node
        inton = collisionargs[0].into_node
        
        surface_point = collisionargs[0].getSurfacePoint(self.node_root)
        contact_pos = collisionargs[0].getContactPos(self.node_root)
        interior_point = collisionargs[0].getInteriorPoint(self.node_root)
        collision_normal = collisionargs[0].getSurfaceNormal(self.node_root)
        
        # what is this?
        prevt = collisionargs[0]
        
        from_tag, from_id = get_info_from_col_node(fromn)
        into_tag, into_id = get_info_from_col_node(inton)
        
        if from_id == into_id:
            from_id = None
            into_id = None
                
        output_d={"from tag":from_tag,
                "from id":from_id,
                "into tag":into_tag,
                "into id":into_id,
                "collision normal":collision_normal,
                "interior point":interior_point,
                "surface point":surface_point}
        
        return output_d
    
    def setup_mouse_ray(self):
        """
        sets up the mouse ray?
        
        step 1 for the crash course
        """
        
        # Make a collision node for our picker ray
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerRay = CollisionRay() 
        self.pickerNode.addSolid(self.pickerRay)
        
        # sets up WHICH collisions are being looked for, 
        # see "bitmasks" in __init__
        self.pickerNode.setFromCollideMask(self.bitmasks["mouseray"]["from"])
        self.pickerNode.setIntoCollideMask(self.bitmasks["mouseray"]["into"])
        
        # this adds the ray to the "list" (not a list, but bear with me)
        # of objects that are being checked for collisions called "node_root"
        # "node_root" is the "input list"
        self.pickerNP = NodePath(self.pickerNode)
        self.pickerNP = self.node_root.attachNewNode(self.pickerNode) # not sure if I need this line.
        self.pickerNP.reparentTo(self.node_root)
        
        
        # this is the actual collision checker
        self.MouseRayTraverser = CollisionTraverser()
        
        # this is the output list for lack of a better term.
        self.CHQ_mouse = CollisionHandlerQueue()
        

        # This means, "if there is a collision with my mouse ray, put it into the CHQ output list"
        self.MouseRayTraverser.addCollider(self.pickerNP, self.CHQ_mouse)
                
        
    def mouse_ray_check(self,mouse_data):
        """
        mouse_data will be 'lensobject, screen_x, screen_y'
        
        passing around the lens object isn't ideal, but since this
        will only happen client side it should be fine.
        
        step 3 for the crash course
        """
        
        # Set the position of the ray based on the mouse position
        (Lens, X, Y), camera_position,camera_hpr = mouse_data
        self.pickerNP.setPos(camera_position)
        self.pickerNP.setHpr(camera_hpr)
        self.pickerRay.setFromLens(Lens, X, Y)
        
        # self.node_root is your input list where all your objects
        # are parented to.
        self.MouseRayTraverser.traverse(self.node_root)
        
        # this is your output list
        self.CHQ_mouse.sortEntries()
        n_entries = self.CHQ_mouse.getNumEntries() 
        
        
        # this whole last part answers the question: 
        # "but WHICH object has my mouse ray collided with?"
        entry_index = 0
        tag_names = ["waypoint","terrain","object","NPC","wall","item","UI"]
        
        mouse_collision_tags = {}
        for tag in tag_names:
            mouse_collision_tags[tag] = []
            
        mouse_3d = None
        
        # this is a bit awkward...
        while entry_index < n_entries and n_entries > 0:
            
            # this is how we get the entry and collision object from the underlying C/C++ part of panda
            collision_entry = self.CHQ_mouse.getEntry(entry_index)
            collision_node = collision_entry.getIntoNode()
            
            # this gets the 3d coordinates of the collision, relative to the root node
            mouse_3d = collision_entry.getSurfacePoint(self.node_root)
            
            # tags are tuples that can be associated with objects
            # as a "name", "data" pair
            # so I'm using the "tag name" to get the id of the object
            for x in tag_names:
                ob_id = collision_node.getTag(x)
                if ob_id == '':
                    continue
                if ob_id not in mouse_collision_tags[x]:
                    mouse_collision_tags[x].append(ob_id)
            
            # loop around.
            entry_index += 1
        
        # clean up the dictionary.
        for tag in tag_names:
            if len(mouse_collision_tags[tag])==0:
                mouse_collision_tags.pop(tag)
        
        # return the last 3d collision point
        # and the dict of all objects, grouped by tag, that the mouse ray has collided with.
        return mouse_3d, mouse_collision_tags
    
    def get_ids_from_collisions(self):
        """
        just detecting and returning ids
        """
        
        collisions = {}
        entry_check = {}
        entries = self.CH_world.getEntries()
        self.CH_world.clearEntries()
        
        for entry in entries:
            collision_dict = self.fetch_objects_from_collision([entry])
            
            # checking for none, because they could be deleted?
            if collision_dict["from id"]!=None and collision_dict["into id"]!=None:
                if collision_dict["from id"] not in collisions:
                    collisions[collision_dict["from id"]]={collision_dict["into id"]:collision_dict}
                
                #if I am not filtering like this, I have multiple entries.
                elif collision_dict["into id"] not in collisions[collision_dict["from id"]]:
                    collisions[collision_dict["from id"]][collision_dict["into id"]]=collision_dict
                    
        return collisions
        
def get_info_from_col_node(node):
    tup = node.getTagKeys()
    tagname = tup[0]
    from_id = node.get_tag(tagname)
    return tagname, from_id
