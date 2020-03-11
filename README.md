# Motion capture armature retarget addon for Blender 2.82

It is very early stage and can map BVH:s to MB-Lab or Makehuman CMU Rigs skeletons only. 

Later we can produce more skeleton maps, and maybe some interactive way to connect bone manually.

Workflow is quite simple, just load your BVH File with regular Blenders import tool. Scale it to match your armature. Attach imported object to source armature and your MB-Lab armature to the target armature. Tweak bone proxies if needed. Bake proxy to action.

Now it contains three bvh-hierarchy maps and few 'user maps'. They lies in Skeleton drawer in same location of the addon itself.
All of them is edittable with any text editor.

*changelog 0.22 version
*Fix crash if you try bake in pose mode
*Ability to skip n frames on bake
*Better 'proxy' identification

Simple video demo
https://youtu.be/NMs20-DGMTo 

Copyright licence is CC-BY
