# panda3d_collisions

This is the code I wrote to handle panda collisions from my game project. Should be obvious I hope, if it isn't open an issue to ask a question or come by on the panda3d discord.

I added some more comments and a basic tutorial / crash course to the script, for mouse ray collisions.

All other collisions work the same way, but with more objects.

The mouse ray is just one object and is checked against a simple list.

E.g. mouseray -> object1, mouseray -> object2

Where normal collisions would also check which is "list squared" and 

E.g. object1 -> object2 and object2 -> object1

which will be exponentially more checks depending on how you set it up.

I have bins for that, only objects inside the same bin are checked because that's how panda does it. node root is the root for the bins and then the bins contain the groups that are being checked.
