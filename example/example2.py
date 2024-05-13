import random
import math

# this is for the inlined object creation, don't worry about it.
from panda3d.core import Texture, GeomNode
from panda3d.core import GeomVertexFormat, GeomVertexData
from panda3d.core import Geom, GeomTriangles,GeomTrifans, GeomVertexWriter

from panda3d.core import Point3
from direct.showbase.ShowBase import ShowBase
from direct.showbase.MessengerGlobal import messenger
from direct.gui.DirectLabel import DirectLabel
from direct.showbase import DirectObject

# self written but public
from panda_collisions import panda_collisions


class WorldObject:
    def __init__(self,myid):
        self.id = myid
        self.verts = []
        self.faces = [[0,1,2,3]] # this has to be a list of lists, with
        # one entry. best don't change this if you don't want to 
        # dig into how object creation works.

class MyDemoTerrain:
    def __init__(self,b):
        # this is necessary because the creator needs to get access
        # to show base to create new objects.
        self.b = b
        
        # this is part of this editor
        self.engine_ob_counter = 0
        self.engine_obs = {}
        self.notes = []
        self.UI_elements = [] # like buttons, not the 3d markers
        self.new_obs = {}
        self.markers = []
        self.marker_objects = []
        self.engine_obs_pos = {}
        self.marker_texts = []
        
        
        self.camera_setup() 
        self.cam_pos = (0,0,1)
        self.wasd_speed = 0.1
        
        self.placed = False
        self.marker_counter =0
        
        
    def get_2d_position(self,pos_3d_tuple):
        pos2d=Point3()
        
        verts=[]
        faces=[]
        
        #bitmask=BitMask32.bit(1)
        fake = make_object(self.b,verts,faces)
        
        fake.setPos(pos_3d_tuple)
        gcp=fake.getPos(self.b.cam)
        inViewpos =self.b.camLens.project(gcp,pos2d)
        fake.removeNode()
        
        return pos2d
    
    def set_x_mouse_diff_2d(self,input_d):
        mouse_3d = input_d["mouse 3d"]
        if mouse_3d != None and self.b.mouseWatcherNode.is_button_down("mouse1"):
            if self.first_point == None:
                self.first_point = self.get_2d_position(mouse_3d)
                self.first_point3d = mouse_3d
            
            self.second_point3d = mouse_3d
            second_point = self.get_2d_position(mouse_3d)
            fp = self.first_point
            sp = second_point
            
            self.x_mouse_diff_2d = fp[0]-sp[0]
        else:
            self.old_hpr = self.cam.getHpr()
            self.first_point = None
            self.x_mouse_diff_2d = None
    
    def cam_rot_update(self):
        h,p,r = self.cam.getHpr()
        old_h,old_p,old_r=self.old_hpr
        if self.x_mouse_diff_2d!=None: 
            # this works, but I don't want it turned on right now.
            M = vector.RotationMatrix(h/360*2*math.pi,(0,0,1))
            h = self.x_mouse_diff_2d*self.heading_scaling
            self.cam.setHpr(h+old_h,p,r)
            #self.dvec=M*self.dvecbase*self.zoom
            
    def camera_setup(self):
        # should be fine, don't move yet.
        print("init")
        self.b.disableMouse()
        self.cam = self.b.camera
        #like focal point
        self.anchor_point = (0,0,0)
        self.anchor_object = None
        self.notmovedfor   = 0
        self.lastanchorpos = (0,0,0)
        self.cam.setPos(0,-10,5)
        self.cam.setHpr(0,-25,0)
    
    def make_new_squares(self,pos):
        self.engine_ob_counter+=1
        #color = (random.random(),random.random(),0,)
        
        verts = [
        (pos[0],  pos[1]  ,pos[2]),
        (pos[0]+1,pos[1]  ,pos[2]),
        (pos[0]+1,pos[1]+1,pos[2]),
        (pos[0],  pos[1]+1,pos[2]),
        ]
        faces = [[0,1,2,3]]
        
        Wo = WorldObject(self.engine_ob_counter)
        Wo.verts = verts
        engine_ob = make_object(self.b, verts, faces, twosided=True)
        
        self.engine_obs[self.engine_ob_counter] = engine_ob
        self.engine_obs_pos[str(pos)] = engine_ob
        Wo.pos = (0,0,0) # it's a bit annoying, but apparently you can either set vert position or this position. so.
        self.new_obs[self.engine_ob_counter] = [Wo,"terrain"]
    
    def main(self,inputs,*args):
        print(inputs)
        if len(inputs) == 3:
            mouse_pos, col_tags, hardwareinputs = inputs
            self.ensure_squares(mouse_pos)
                       
                
    def ensure_squares(self,mouse_pos=None):
        # make new squares
        # initialze if empty
        if len(self.engine_obs_pos)==0 or mouse_pos==None:
            mouse_pos=(0,0,0)
        x = round(mouse_pos[0],0)
        y = round(mouse_pos[1],0)
        
        yw = 7 # adjust to taste.
        xw = 7
        cx = 0
        
        xoffset=int.__floordiv__(xw,2)
        yoffset=int.__floordiv__(yw,2)

        # that' probably relatively expensive to test, I can 
        # there are easier ways to do this...
        while cx < xw:
            cy = 0
            while cy < yw:
                pos = (x -xoffset +cx,y-yoffset+cy,0)
                if str(pos) not in self.engine_obs_pos:
                    self.make_new_squares(pos)
                cy += 1
            cx += 1 
        
        
        
class Wrapper:
    def __init__(self):
        self.b = ShowBase()
        self.editor = MyDemoTerrain(self.b)
        self.collisions = panda_collisions.CollisionWrapper()
        self.collisions.setup_mouse_ray()
        self.event_handler = DirectObject.DirectObject()
        self.event_handler.accept("mouse1",self.pass_on,["left mouse"])
        self.inputs = []
        
        self.buttons_move_actions = {
                        "mouse1":"left mouse",
                        "mouse3":"right mouse",
                        "a":"a"}
        
        self.create_move_task()
        
    def pass_on(self,action):
        if action not in self.inputs:
            self.inputs.append(action)
            
    def create_move_task(self):
        print("move task created")
        self.b.taskMgr.add(move_task,"Move Task",extraArgs=[self],appendTask=True)
        
def move_task(*args):
    #somewhat selfexplanatory? It's the watcher thing that
    #tracks movement inputs
    
    Task=args[1]
    wrapper=args[0]
    is_down = wrapper.b.mouseWatcherNode.is_button_down
    
    for mb in wrapper.buttons_move_actions:
        if is_down(mb):
            wrapper.pass_on(wrapper.buttons_move_actions[mb])
                
    return Task.cont



def makecoloredPoly(verts,faces,color_tuple=None):
    """
    this function is inlined from my other project https://github.com/BMaxV/panda_object_creation
    
    this function creates the polygon that will be added to the geom
    datastructure"""
    verts = verts.copy()    
    old_vert_len = len(verts)
    center_ids = []
    for f in faces:
        vl = []
        for p in f:
            vl.append(verts[p])
        center_p = calculate_center(vl)
        verts.append(center_p)
        center_ids.append(len(verts)-1)
    
    tformat = GeomVertexFormat.getV3t2()
    vdata = create_vdata(verts,color_tuple)
    poly = Geom(vdata)
    c=0
    flb=0
    while c < len(faces):
        tris = GeomTrifans(Geom.UHStatic)
        face=faces[c]
        
        tris.addVertex(center_ids[c])
        for i in face:
            tris.addVertex(i)
        tris.addVertices(face[-1],face[0])
        tris.closePrimitive()
        poly.addPrimitive(tris)
        flb+=len(face)
        c+=1
    
    return poly
def make_object(base,verts=[(0,0,0),(1,0,0),(1,1,0),(0,1,0)],
                    faces_vert_index_list=[[0,1,2,3]],
                    twosided=False,
                    tag_tuple=("terrain","1"),
                    collision_mask=None,
                    color=None,
                    texture=None,
                    transparent=0,
                    ):
    
    """
    this function is inlined from my other project https://github.com/BMaxV/panda_object_creation
    
    Don't worry about it or look at it there, i have more comments there.
    
    this function creates a whole object
    you can just create individual faces as well, but there
    are gains for doing it in bulk.
    
    
    """
    
    faces_vis=faces_vert_index_list
        
    snode = GeomNode('Object')
    
    if color !=None and texture!=None:
        raise ValueError
    if texture==None:
        poly = makecoloredPoly(verts,faces_vis,color)
    else:
        poly = make_textured_poly(verts,faces_vis)
    
    snode.addGeom(poly)
    
    if type(base).__name__=="ShowBase":
        ob = base.render.attachNewNode(snode)
    else:
        ob=NodePath(snode)
        ob.reparentTo(base)
        
    assert transparent in [0,1]
    ob.setTransparency(transparent)
    
    if collision_mask!=None:
        ob.node().setIntoCollideMask(collision_mask)
    
    if tag_tuple!=None:
        ob.setTag(*tag_tuple) 
    ob.setTwoSided(twosided)
    
    return ob

def calculate_center(point_list):
    """
    this function is inlined from my other project https://github.com/BMaxV/panda_object_creation
    
    Don't worry about it or look at it there, i have more comments there.
    """
    center_p=[0,0,0]
    for p in point_list:
        center_p[0]+=p[0]
        center_p[1]+=p[1]
        center_p[2]+=p[2]
    center_p[0]=center_p[0]/len(point_list)
    center_p[1]=center_p[1]/len(point_list)
    center_p[2]=center_p[2]/len(point_list)
    return center_p

   
def create_vdata(verts,color_tuple):
    """
    this function is inlined from my other project https://github.com/BMaxV/panda_object_creation
    
    Don't worry about it or look at it there, i have more comments there.
    """
    #this is the format we'll be using.
    format = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData('convexPoly', format, Geom.UHStatic)

    vdata.setNumRows(len(verts))
    
    # these are access shortcuts
    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')
    
    # tells the format how many vertices we'll create
    
    if color_tuple == None:
        vran1 = random.random()
        vran2 = random.random()
        #color_t=random.choice([(255*random.random(),0,0),(0,255*random.random(),0)])#,(0,0,255)])
        color_t = (1*vran1, 1*vran2, 0)#,(0,255*random.random(),0)])#,
        #color_t=(0,0,255)
    else:
        color_t = color_tuple
        
    #set the data for each vertex.
    for p in verts:
        vertex.addData3(tuple(p))
        color.addData4f(*color_t[:],0.5)
        normal.addData3(0,0,1)
        #do i need normals?
    return vdata



def main():
    W = Wrapper()
    inputs = []
    while True:
        inputs += [W.inputs]
        W.inputs=[]
        W.b.taskMgr.step()
        W.editor.main(inputs)
        inputs = []
        W.collisions.update({"create complex":W.editor.new_obs})
        W.editor.new_obs = {}
        if W.b.mouseWatcherNode.hasMouse():
            mpos = W.b.mouseWatcherNode.getMouse() 
            campos = W.editor.cam.getPos()
            camhpr = W.editor.cam.getHpr()
            mouse_data = ((W.b.camNode,mpos.getX(),mpos.getY()),campos,camhpr)
            
            pos,tags = W.collisions.mouse_ray_check(mouse_data)
            inputs += [pos,tags]
        
if __name__ == "__main__":
    main()
