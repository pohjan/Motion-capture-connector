# Motion capture armature retarget addon for Blender 2.82

It is very early stage and can map BVH:s to MB-Lab skeleton only. I made this for my own needs, any existing armature retarget tools does not work for me. Now it works fine with MB-Lab humans (Not IK rig), so I decided publish this now at this stage.

Later we can produce more skeleton hierarky maps, and maybe some interactive way to connect bone manually.

Workflow is quite simple, just load your BVH File with regular Blenders import tool. Scale it to match your armature. Attach imported object to source armature and your MB-Lab armature to the target armature. Tweak bone proxies if needed. Bake proxy to action.

Now it contains three bvh-hierarchy maps and few 'user maps'. They lies in Skeleton drawer in same location of the addon itself.
All of them is edittable eith any text editor.


Copyright licence is CC-BY
