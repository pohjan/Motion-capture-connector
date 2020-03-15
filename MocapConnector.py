bl_info = {
    "name": "Mocap connector",
    "author": "Petri Pohjanmies",
    "version": (0, 24),
    "blender": (2, 80, 0),
    "location": "Object data panel > Armature",
    "description": "Motion capture connection tools",
    "warning": "",
    "wiki_url": "https://github.com/pohjan/Motion-capture-connector/wiki",
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
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        mytool = scene.mconn

        type = context.active_object.type
        
        #way to store items in ui, not saved in .blend,,
        #self.ownprop="Test"

        if type=="ARMATURE" or "mcproxy" in context.active_object:

            layout.label(text="Source")
            row = layout.row()
            row.label(text=mytool.mcrtactor,icon="ARMATURE_DATA")
            row.operator("scene.mcrtactor")
            row = layout.row()
            row.prop(mytool,"actorskeletonmode",icon="OUTLINER_OB_ARMATURE")
            
            layout.row().separator()
            #layout.label(text="-")
            
            layout.label(text="Target")
            row = layout.row()
            row.label(text=mytool.mcrtdestination,icon="ARMATURE_DATA")
            row.operator("scene.mcrtdestination")
            row = layout.row()
            row.prop(mytool,"targetskeletonmode",icon="OUTLINER_OB_ARMATURE")
            
            layout.row().separator()
            row = layout.row()
            
            layout.row().separator()
            row.operator("scene.mcrtmake", icon="LINKED")
            
            layout.label(text="Tweak options")
            
            row = layout.row()
            row.prop(mytool,"ilocpelvis")
            row = layout.row()
            row.prop(mytool,"irotshoulders")
            row = layout.row()
            row.prop(mytool,"irotneck")
            
            layout.row().separator()
            
            row = layout.row()
            row.label(text="Bake options")
            row = layout.row()
            row.prop(mytool,"frameskip")
            row = layout.row()
            row.prop(mytool,"oldaction")
            row = layout.row()
            dou=row.operator("scene.mcrtfini",icon="ACTION")
            if "Joint-Pelvis" not in bpy.data.objects:
                row.enabled=False

class makeArmatureProxy(bpy.types.Operator):
    """Make armature proxy for adjust bones"""
    bl_idname = "scene.mcrtmake"
    bl_label = "Connect armatures"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        successo=makeProxies(self,context)
        if successo==1:
            updateConstraints(self, context)
        
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
        mytool = scene.mconn
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
        mytool = scene.mconn
        mytool.mcrtdestination=context.active_object.name
        return {'FINISHED'}



def finalise():
    scene = bpy.context.scene
    mytool = scene.mconn
    
    current_mode = bpy.context.object.mode
    
    myobj=bpy.context.scene.objects[mytool.mcrtdestination]
    skip=mytool.frameskip
    acmode=mytool.oldaction
    
    bpy.ops.object.mode_set ( mode = "OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    
    myobj.select_set(True)
    bpy.context.view_layer.objects.active = myobj
    
    print ("Bake started - please wait")
    
    bpy.ops.object.mode_set ( mode = "POSE")
    
    bpy.ops.pose.select_all(action='SELECT')

    start=bpy.context.scene.frame_start
    end=bpy.context.scene.frame_end
    
    bpy.ops.nla.bake(frame_start=start, frame_end=end, visual_keying=True, step=skip, use_current_action=acmode, clear_constraints=True, bake_types={'POSE'})
    
    bpy.ops.object.mode_set ( mode = current_mode)
    print ("Bake ready")
    killProxies()


def makeProxies(operator,context):
    killProxies()
    generateProxies(operator,context)


def killProxies():
    bpy.ops.object.mode_set ( mode = "OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.data.objects:
        if "mcproxy" in ob:
            ob.select_set(True)
    bpy.ops.object.delete()


#Proxymaker itself
def generateProxies(operator,context):
    scene = bpy.context.scene
    mytool = scene.mconn
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

    if mytool.mcrtactor=="" or mytool.mcrtdestination=="":
        operator.report({'ERROR'},"Source ot target not an armature")
        return 0
    if not mytool.mcrtactor in bpy.context.scene.objects:
        operator.report({'ERROR'},"Source not exits")
        return 0
    if not mytool.mcrtdestination in bpy.context.scene.objects:
        operator.report({'ERROR'},"Target not exits")
        return 0
    sourceob=bpy.context.scene.objects[mytool.mcrtactor]
    targetob=bpy.context.scene.objects[mytool.mcrtdestination]
    
    if sourceob.type=="ARMATURE":
        targetob["mcstructure"]=targetbones
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
                        makeProxy(bone,sourceob,targetob,b[0],found,1,a[1],a[2],a[3], a[4],a[5],a[6] ,b[1],b[2],b[3], b[4],b[5],b[6])
                        #targetob["mcpelvisbone"]=b[0]
                        print (targetob)
                    else:
                        makeProxy(bone,sourceob,targetob,b[0],found,0,a[1],a[2],a[3], a[4],a[5],a[6] ,b[1],b[2],b[3], b[4],b[5],b[6])

    return 1

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


def makeProxy( bone,arma,targetob,destname,keyname, locrot ,srx,sry,srz ,sox,soy,soz ,drx,dry,drz ,dox,doy,doz ):
    
    bonename=bone.name
    
    #Generate actor proxy
    
    ob=bpy.data.objects.new("Joint-"+keyname,None)
    bpy.context.scene.collection.objects.link ( ob )
    ob.empty_display_size=.02
    ob.empty_display_type="SPHERE"
    ob["mcproxy"]=True
    

    loc=arma.location+bone.head
    ob.location=loc
    
    con=ob.constraints.new("COPY_TRANSFORMS")
    con.target=arma
    con.subtarget=bone.name
    con.name = "MCAP Transforms"
    #Generate rotation proxy
    
    targetbone=getBoneByName(targetob,destname)
    if targetbone==0:
        print ("Bone",destname,"not exists in armature")
        return
    
    ob2=bpy.data.objects.new("Tweak-"+keyname,None)    
    bpy.context.scene.collection.objects.link ( ob2 )
    ob2.empty_display_size=.26
    ob2.empty_display_type="SINGLE_ARROW"
    ob2["mcproxy"]=True
    
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
    tarcon.name = "MCAP Rotations"
    tarcon.target=ob2
    
    if locrot==1:
        print ("locrot")
        tarcon=targetbone.constraints.new("COPY_LOCATION")
        tarcon.name = "MCAP Location"
        tarcon.target=ob2
    
def getBoneByName(ob,name):
    cbone=0
    carma=0
    scene = bpy.context.scene
    mytool = scene.mconn
    
    if ob.type=="ARMATURE":
        for bone in ob.pose.bones:
            if bone.name==name:
                cbone=bone
                carma=ob
                print ("Target exists:"+cbone.name)
    return cbone
    
def updateConstraints(self,context):
    scene = bpy.context.scene
    mytool = scene.mconn
    
    ob=bpy.context.scene.objects[mytool.mcrtdestination]
    #bone=ob.pose.bones[ob["mcpelvisbone"]]
    
    bonelist=ob["mcstructure"]
    
    #Pelvis location i
    bone=ob.pose.bones[bonelist["Pelvis"][0]]
    con=bone.constraints["MCAP Location"]
    con.influence=mytool.ilocpelvis
    
    #Shoulders rotation i
    bone=ob.pose.bones[bonelist["LShoulder"][0]]
    con=bone.constraints["MCAP Rotations"]
    con.influence=mytool.irotshoulders
    bone=ob.pose.bones[bonelist["RShoulder"][0]]
    con=bone.constraints["MCAP Rotations"]
    con.influence=mytool.irotshoulders
    
    #Neck rotation i
    bone=ob.pose.bones[bonelist["Neck"][0]]
    con=bone.constraints["MCAP Rotations"]
    con.influence=mytool.irotneck
    
    return None


class PG_MyProperties (PropertyGroup):

    oldaction : BoolProperty(
        name="Overwrite existing action",
        description="If not selected then new action appears",
        default = False
        )

    frameskip : IntProperty(
        name = "Skipping frames",
        description="Number of skipped frames",
        default = 1,
        min = 1,
        max = 10
        )
    
    ilocpelvis : FloatProperty(
        name = "Pelvis location influence",
        description="Influence of pelvis location",
        default = 1,
        update = updateConstraints,
        min = 0,
        max = 1,
        step = .5
        )
    
    irotshoulders : FloatProperty(
        name = "Shoulders rotation influence",
        description="Influence of shoulders rotation",
        default = 1,
        update = updateConstraints,
        min = 0,
        max = 1,
        step = .5
        )
    irotneck : FloatProperty(
        name = "Neck rotation influence",
        description="Influence of neck rotation",
        default = 1,
        update = updateConstraints,
        min = 0,
        max = 1,
        step = .5
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
               ('Target-Rigify', "Rigify", ""),
               ('Target-User1', "Target-User1", ""),
               ('Target-User2', "Target-User2", ""),
               ('Target-User3', "Target-User3", ""),
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
    bpy.types.Scene.mconn = PointerProperty(type=PG_MyProperties)

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
    del bpy.types.Scene.mconn  # remove PG_MyProperties 

if __name__ == "__main__":
    register()
