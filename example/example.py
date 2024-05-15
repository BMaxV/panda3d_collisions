from panda_collisions import panda_collisions

# from direct.showbase.ShowBase import ShowBase
from panda3d.core import LVector3f, LPoint3f


class Wrapper:
    def __init__(self):

        self.b = None

        # uncomment this if you want a window
        # self.b = ShowBase()

        self.collisions = panda_collisions.CollisionWrapper()
        self.collisions.setup_mouse_ray()  # optional, really.
        self.single_update = False


expected_output = {
    'myNPC2':
    {'myNPC1':
        {'from tag': 'NPC', 'from id': 'myNPC2', 'into tag': 'NPC', 'into id': 'myNPC1',  # who is colliding with what?
         'collision normal': LVector3f(1, 0, 0), 'interior point': LPoint3f(-0.2, 0, 0), 'surface point': LPoint3f(0.3, 0, 0)}},  # data for the collision.
    'myNPC1':
    {'myNPC2':
        {'from tag': 'NPC', 'from id': 'myNPC1', 'into tag': 'NPC', 'into id': 'myNPC2',
         'collision normal': LVector3f(-1, 0, 0), 'interior point': LPoint3f(0.3, 0, 0), 'surface point': LPoint3f(-0.2, 0, 0)}}
}

# the collision is symmetric, because we can have asymmetric collisions too.
# e.g. the mouse only collides INTO objects,
# but the objects don't collide INTO the mouse.


def main():
    W = Wrapper()
    inputs = []

    # this is the main loop for the example.
    while True:

        # this makes the panda simulation "progress"
        # but we don't actually need it for the collisions.
        #
        # W.b.taskMgr.step()

        # this is done a single time, because it's the example, but
        # this is how you would otherwise create, update, destroy collision shapes.
        if not W.single_update:

            # this creates default spheres for 3 objects
            # format is ("unique id","predefined collision group")
            # check the source for details.
            W.collisions.update(
                {"create": {"myNPC1": "NPC", "myNPC2": "NPC", "myNPC3": "NPC"}})
            W.collisions.update({"update": {
                # setting position and rotation
                "myNPC1": ((0, 0, 0), (0, 0, 0)),
                "myNPC2": ((0.1, 0, 0), (0, 0, 0)),
                "myNPC3": ((5, 0, 0), (0, 0, 0))}})

            W.single_update = True

        # this should work if the camera is pointed at the objects.
        if W.b != None:
            if W.b.mouseWatcherNode.hasMouse():
                mpos = W.b.mouseWatcherNode.getMouse()
                campos = W.b.cam.getPos()
                camhpr = W.b.cam.getHpr()
                mouse_data = ((W.b.camNode, mpos.getX(),
                              mpos.getY()), campos, camhpr)
                pos, tags = W.collisions.mouse_ray_check(mouse_data)
                print(pos, tags)
                input()

        # this is what you really want.
        collisions = W.collisions.collision_checks()

        # print(collisions == expected_output)
        print(collisions)
        input()


if __name__ == "__main__":
    main()
