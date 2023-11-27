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


# this one for help? https://discourse.panda3d.org/t/magical-collision-scene-optimizer/28978

class CollisionWrapper:
    def __init__(self,client=True):        
        self.node_root = NodePath("node_root")
        self.collision_objects = {}
        self.collision_bins = {}
        
        self.bitmasks={"mouseray":
            {"from":BitMask32(0b0111),"into":BitMask32(0b0000)},
                        "terrain":
            {"from":BitMask32(0b0000),"into":BitMask32(0b0100)},
                        "waypoint": # things that are already defined as waypoints
            {"from":BitMask32(0b0000),"into":BitMask32(0b0100)},
                        "item": # things that are not yet defined as waypoints, but are interactable.
            {"from":BitMask32(0b0000),"into":BitMask32(0b0100)},
                        "players":
            {"from":BitMask32(0b0001),"into":BitMask32(0b0011)},
                        "NPC":
            {"from":BitMask32(0b0001),"into":BitMask32(0b0011)},
                        "wall":
            {"from":BitMask32(0b0001),"into":BitMask32(0b0011)},
            
            }
        
        
        self.cTrav = CollisionTraverser()
        self.client_mouse_hover = client
        
        if client:
            self.setup_mouse_click()
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
        """this will require a dictionary as input"""
        # tags I want... Actors, terrain, UI, Walls/structures?
        # then check the queue for the collisions I have found.
        
        
        
        if "create" in input_d:
            for ob_id in input_d["create"]:
                
                tag_name = input_d["create"][ob_id]
                self.create_collision_node(ob_id,tag_name)
        
        if "create complex" in input_d:
            for wo in input_d["create complex"]:
                
                tagname=input_d["create complex"][wo][0]
                self.create_complex(wo,tagname=tagname)
            
        
        if "update" in input_d:
            for ob_id in input_d["update"]:
                if ob_id not in self.collision_objects:
                    continue
                    
                self.collision_objects[ob_id].setPos(*tuple(input_d["update"][ob_id]))
                
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
        """ """
        
        collision_mask=self.bitmasks[tagname]["into"]
        my_ob=panda_object_create_load.make_object(self.node_root,world_object.verts,world_object.faces,tag_tuple=(tagname,str(world_object.id)),collision_mask=collision_mask)
        self.collision_objects[world_object.id] = my_ob
        
        my_ob.setPos(*world_object.pos)
    
    def clear_all(self):
        for key in self.collision_objects:
            ob=self.collision_objects[key]
            ob.removeNode()
        
        self.collision_objects={}
    
    def collision_checks(self):
        #actually look for collisions
        self.cTrav.traverse(self.node_root)
        collision_d = self.get_ids_from_collisions()
        
        return collision_d
        
        if False:
                if type(world_ob).__name__=="ContainerProjectile":
                    
                    tag_tuple=("projectile",str(world_ob.id))
                    collision_mask=BitMask32.bit(1)
                    self.attach_collision_node(engine_ob,tag_tuple)
        
        
    def create_collision_node(self,ob_id,tag_name):
        """
        so the collision objects gets the same tag as the worldobject
        """
        
        # ok,so, terrain stuff is difficult because I'm not
        # previously I was just using the terrian geometry.
        
        # define node type and shape
        col_Node = CollisionNode("general_col_node")
        col_NodeNP=NodePath(col_Node)
        
        # this is for tracking
        # node root because cTrav will iterate over it
        col_NodeNP.reparentTo(self.node_root)
        # tag is being used to recover the object
        col_NodeNP.set_tag(tag_name,str(ob_id))
        # object dict for updating and deleting.
        self.collision_objects[ob_id]=col_NodeNP
        
        col_body = CollisionSphere((0,0,0),0.3)
        col_Node.addSolid(col_body)
        
        # set mask
        col_Node.setFromCollideMask(self.bitmasks[tag_name]["from"])
        col_Node.setIntoCollideMask(self.bitmasks[tag_name]["into"])
        
        #set it up so it's being tracked.
        self.cTrav.addCollider(col_NodeNP,self.CH_world)
        
    def fetch_objects_from_collision(self,collisionargs):
        #I should unpack these.
        
        fromn = collisionargs[0].from_node
        inton = collisionargs[0].into_node
                
        collision_normal=collisionargs[0].getSurfaceNormal(self.node_root)
        
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
                "collision normal":collision_normal}
        
        return output_d
    
    def setup_mouse_click(self):
        """
        this is the optional collision traverser for the client.
        e.g. if stuff is being rendered, go through the iteration with
        the ray and check when the mouse hovers on. the server doesn't need this however.
        """
        #from the chess sample
        self.picker = CollisionTraverser() 
        self.CHQ_mouse = CollisionHandlerQueue()
        # Make a collision node for our picker ray
        self.pickerNode = CollisionNode('mouseRay')
        # Attach that node to the camera since the ray will need to be positioned
        # relative to it
        self.pickerNP = NodePath(self.pickerNode)
        
        # this is for tracking
        # node root because cTrav will iterate over it
        self.pickerNP.reparentTo(self.node_root)
        
        self.pickerNP = self.node_root.attachNewNode(self.pickerNode)
        
        self.pickerNode.setFromCollideMask(self.bitmasks["mouseray"]["from"])
        self.pickerNode.setIntoCollideMask(self.bitmasks["mouseray"]["into"])

        self.pickerRay = CollisionRay()  
        # Add it to the collision node
        self.pickerNode.addSolid(self.pickerRay)
        # Register the ray as something that can cause collisions
        self.picker.addCollider(self.pickerNP, self.CHQ_mouse)
        
    def mouse_ray_check(self,mouse_data):
        """
        mouse_data will be 'lensobject, screen_x, screen_y'
        
        passing around the lens object isn't ideal, but since this
        will only happen client side it should be fine.
        """
        
        # highly recommend reading the manual if you're reading comments
        # yes, do it again.
        
        mouse_collision_tags = {}
        mouse_3d = None
        
        # Set the position of the ray based on the mouse position
        (Lens, X, Y), camera_position,camera_hpr = mouse_data
        self.pickerNP.setPos(camera_position)
        self.pickerNP.setHpr(camera_hpr)
        self.pickerRay.setFromLens(Lens, X, Y)
        
        # this should be where the nodes are.
        self.picker.traverse(self.node_root)
        self.CHQ_mouse.sortEntries()
        
        n_entries =self.CHQ_mouse.getNumEntries() 
        
        entry_index = 0
        tag_names=["waypoint","terrain","object","NPC","wall","item"]
        
        for tag in tag_names:
            mouse_collision_tags[tag]=[]
            
        while entry_index < n_entries and n_entries > 0:
            collision_entry=self.CHQ_mouse.getEntry(entry_index)
            collision_node=collision_entry.getIntoNode()
            mouse_3d = collision_entry.getSurfacePoint(self.node_root)
            for x in tag_names:
                ob_id = collision_node.getTag(x)
                if ob_id=='':
                    continue
                if ob_id not in mouse_collision_tags[x]:
                    if ob_id not in mouse_collision_tags[x]:
                        mouse_collision_tags[x].append(ob_id)
            entry_index += 1
        
        for tag in tag_names:
            if len(mouse_collision_tags[tag])==0:
                mouse_collision_tags.pop(tag)
        
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
