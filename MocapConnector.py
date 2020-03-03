bl_info = {
    "name": "Mocap connector",
    "author": "Petri Pohjanmies",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "Object data panel > Armature",
    "description": "Motion capture connection tools",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}


import bpy,math,os,mathutils

from bpy.utils import ( register_class, unregister_class )

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )


class LayoutDemoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Mocap connector tools"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        mytool = scene.my_tool

        type = context.active_object.type

        if type=="ARMATURE":

            layout.label(text="Source armature")
            row = layout.row()
            row.label(text=mytool.mcrtactor)
            row.operator("scene.mcrtactor")
            row = layout.row()
            row.prop(mytool,"actorskeletonmode")
            
            
            layout.label(text="-")
            
            layout.label(text="Target armature")
            row = layout.row()
            row.label(text=mytool.mcrtdestination)
            row.operator("scene.mcrtdestination")
            row = layout.row()
            row.prop(mytool,"targetskeletonmode")
            
            layout.label(text="-")
            
            layout.label(text="Actions")
            row = layout.row()
            
            row.operator("scene.mcrtmake")
            row = layout.row()
            row.operator("scene.mcrtfini")

class makeArmatureProxy(bpy.types.Operator):
    """Make armature proxy for adjust bones"""
    bl_idname = "scene.mcrtmake"
    bl_label = "Connect armatures"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        makeProxies()
        return {'FINISHED'}
 
class bakeArmatureProxy(bpy.types.Operator):
    """Apply constraints to action"""
    bl_idname = "scene.mcrtfini"
    bl_label = "Bake proxy to action"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        finalise()
        return {'FINISHED'}


class setActor(bpy.types.Operator):
    """Set active armature to source"""
    bl_idname = "scene.mcrtactor"
    bl_label = "Set source armature"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        mytool.mcrtactor=context.active_object.name
        return {'FINISHED'}

class setDestination(bpy.types.Operator):
    """Set active armature to target"""
    bl_idname = "scene.mcrtdestination"
    bl_label = "Set target armature"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        mytool.mcrtdestination=context.active_object.name
        return {'FINISHED'}



def finalise():
    scene = bpy.context.scene
    mytool = scene.my_tool
    
    myobj=bpy.context.scene.objects[mytool.mcrtdestination]
    
    bpy.ops.object.select_all(action='DESELECT')
    
    myobj.select_set(True)
    bpy.context.view_layer.objects.active = myobj
    
    print ("Bake started - please wait")
    current_mode = bpy.context.object.mode
    bpy.ops.object.mode_set ( mode = "POSE")
    
    bpy.ops.pose.select_all(action='SELECT')

    start=bpy.context.scene.frame_start
    end=bpy.context.scene.frame_end
    
    bpy.ops.nla.bake(frame_start=start, frame_end=end, visual_keying=True, clear_constraints=True, bake_types={'POSE'})
    
    bpy.ops.object.mode_set ( mode = current_mode)
    print ("Bake ready")
    killProxies()


def makeProxies():
    killProxies()
    generateProxies()


def killProxies():
    bpy.ops.object.mode_set ( mode = "OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        if ob.name[0:5]=="Proxy":
            ob.select_set(True)
    bpy.ops.object.delete()


#Proxymaker itself
def generateProxies():
    scene = bpy.context.scene
    mytool = scene.my_tool
    #Bone match list

    bones={ "Hips"   :"pelvis",
        "ToSpine":"spine01",
        "Spine":"spine02",
        "Spine1":"spine03",
        "Neck":"neck",
        "Head":"head",
        "LeftUpLeg":"thigh_L",
        "RightUpLeg":"thigh_R",
        "LeftLeg":"calf_L",
        "RightLeg":"calf_R",
        "LeftFoot":"foot_L",
        "RightFoot":"foot_R",
        "LeftShoulder":"clavicle_L",
        "RightShoulder":"clavicle_R",
        "LeftArm":"upperarm_L",
        "RightArm":"upperarm_R",
        "LeftForeArm":"lowerarm_L",
        "RightForeArm":"lowerarm_R",
        "LeftHand":"hand_L",
        "RightHand":"hand_R"}

    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)

    #open source bones
    sfile=open(directory+"/Skeletons/"+mytool.actorskeletonmode+".txt","r")
    sourcebones=readSkeleton(sfile)
    sfile.close()
    
    #open dest bones
    sfile=open(directory+"/Skeletons/"+mytool.targetskeletonmode+".txt","r")
    targetbones=readSkeleton(sfile)
    sfile.close()

    pelvisbone="Hips"

    sourceob=bpy.context.scene.objects[mytool.mcrtactor]
    targetob=bpy.context.scene.objects[mytool.mcrtdestination]
    
    if sourceob.type=="ARMATURE":
        for bone in sourceob.pose.bones:
            found=0
            for sbone in sourcebones:
                find=sourcebones[sbone]
                if find[0]==bone.name:
                    found=sbone
            
            if found!=0:
                b=targetbones[found]
                a=sourcebones[found]
                if b[0]!="<null>":
                    print (bone.name,"found in key",found,"/",b[0])
                    if bone.name==pelvisbone:
                        makeProxy(bone,sourceob,targetob,b[0],1,a[1],a[2],a[3], a[4],a[5],a[6] ,b[1],b[2],b[3], b[4],b[5],b[6])
                    else:
                        makeProxy(bone,sourceob,targetob,b[0],0,a[1],a[2],a[3], a[4],a[5],a[6] ,b[1],b[2],b[3], b[4],b[5],b[6])

def readSkeleton(f):
    count=0
    skeleton={}
    while True: 
        count += 1
  
        # Get next line from file 
        line = f.readline() 
  
        # if line is empty 
        # end of file is reached 
        if not line: 
            break
        line=line.strip()
        if line[0:5]=="Name:":
            name=line
            print (name)
    
        if line[0:1]=="@":
            line=line[1:]
            key,bone,rx,ry,rz,ox,oy,oz=line.split(",")
            skeleton[key]=[bone,rx,ry,rz,ox,oy,oz]
    
    return skeleton


def makeProxy( bone,arma,targetob,destname,locrot ,srx,sry,srz ,sox,soy,soz ,drx,dry,drz ,dox,doy,doz ):
    
    bonename=bone.name
    
    #Generate actor proxy
    
    ob=bpy.data.objects.new("Proxy",None)
    bpy.context.scene.collection.objects.link ( ob )
    ob.empty_display_size=.02
    ob.empty_display_type="SPHERE"
    

    loc=arma.location+bone.head
    ob.location=loc
    
    con=ob.constraints.new("COPY_TRANSFORMS")
    con.target=arma
    con.subtarget=bone.name
    
    #Generate rotation proxy
    
    targetbone=getBoneByName(targetob,destname)
    if targetbone==0:
        print ("Bone",destname,"not exists in armature")
        return
    
    ob2=bpy.data.objects.new("Proxy-"+destname,None)    
    bpy.context.scene.collection.objects.link ( ob2 )
    ob2.empty_display_size=.26
    ob2.empty_display_type="SINGLE_ARROW"
    
    loct=targetob.location+targetbone.head
    
    #Rotate x z y -> x y z ????
    
    rx,ry,rz=targetbone.matrix.to_euler()

    rx=rx-(math.pi/2.0)
    #rz=rz+(math.pi/2.0)

   
    ob2.location=[0,0,0]

    ob2.parent = ob
    #ob2.rotation_euler=[rx,rz,-ry]
    ob2.rotation_euler=[(float(srx)+float(drx))/360*2*math.pi,(float(sry)+float(dry))/360*2*math.pi,(float(srz)+float(drz))/360*2*math.pi]
    ob2.convert_space(from_space='LOCAL', to_space='WORLD')
    
    loc = ob2.location
    ob2.location = loc + mathutils.Vector((float(sox)+float(dox),float(soy)+float(doy),float(soz)+float(doz)))
    
    #Make copy rotation to bones
    for con in targetbone.constraints:
        targetbone.constraints.remove(con)
    tarcon=targetbone.constraints.new("COPY_ROTATION")
    tarcon.target=ob2
    
    if locrot==1:
        print ("locrot")
        tarcon=targetbone.constraints.new("COPY_LOCATION")
        tarcon.target=ob2
    
def getBoneByName(ob,name):
    cbone=0
    carma=0
    scene = bpy.context.scene
    mytool = scene.my_tool
    
    if ob.type=="ARMATURE":
        for bone in ob.pose.bones:
            if bone.name==name:
                cbone=bone
                carma=ob
                print ("Target exists:"+cbone.name)
    return cbone
    

class PG_MyProperties (PropertyGroup):

    my_bool : BoolProperty(
        name="Enable or Disable",
        description="A bool property",
        default = False
        )

    my_int : IntProperty(
        name = "Int Value",
        description="A integer property",
        default = 23,
        min = 10,
        max = 100
        )

    my_float : FloatProperty(
        name = "Float Value",
        description = "A float property",
        default = 23.7,
        min = 0.01,
        max = 30.0
        )

    my_float_vector : FloatVectorProperty(
        name = "Float Vector Value",
        description="Something",
        default=(0.0, 0.0, 0.0), 
        min= 0.0, # float
        max = 0.1
    ) 

    mcrtactor : StringProperty(
        name="User Input",
        description=":",
        default="",
        maxlen=1024,
        )
        
    mcrtdestination : StringProperty(
        name="User Input",
        description=":",
        default="",
        maxlen=1024,
        )

    actorskeletonmode : EnumProperty(
        name="Skeleton model:",
        description="Apply Data to attribute.",
        items=[ ('Source-Biped', "5-Spinebones", ""),
               ('Source-3Spines', "3-Spinebones", ""),
               ('Source-dancedb.eu', "dancedb.eu BVH", ""),
               ('Source-User1', "Source-User1", ""),
               ('Source-User2', "Source-User2", ""),
               ('Source-User3', "Source-User3", ""),
               ]
        )
        
    targetskeletonmode : EnumProperty(
        name="Skeleton model:",
        description="Apply Data to attribute.",
        items=[ ('Target-MBLab', "MB-Lab No-IK", ""),
               ('Target-Makehumancmu', "Makehuman cmu db rig", ""),
                ('A3', "-", ""),
               ]
        )

classes = (
    PG_MyProperties,
   
)


def register():
    for cls in classes:
        register_class(cls)
    #
    bpy.utils.register_class(LayoutDemoPanel)
    bpy.utils.register_class(makeArmatureProxy)
    bpy.utils.register_class(bakeArmatureProxy)
    bpy.utils.register_class(setActor)
    bpy.utils.register_class(setDestination)
    #bpy.utils.register_class(actorProps)
    bpy.types.Scene.my_tool = PointerProperty(type=PG_MyProperties)

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    #
    bpy.utils.unregister_class(LayoutDemoPanel)
    bpy.utils.unregister_class(makeArmatureProxy)
    bpy.utils.unregister_class(bakeArmatureProxy)
    bpy.utils.unregister_class(setActor)
    bpy.utils.unregister_class(setDestination)
    #bpy.utils.unregister_class(actorProps)
    del bpy.types.Scene.my_tool  # remove PG_MyProperties 

if __name__ == "__main__":
    register()
