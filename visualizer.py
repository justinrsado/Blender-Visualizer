import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import bpy
from bpy.types import Operator
import numpy as np
install("scipy")
import scipy.signal as signal
from mathutils import Vector
from copy import deepcopy

def get_seq_magnitudes():
    total = 0

    if bpy.context.scene.sequence_editor is None:
        return 0
    
    sequences = bpy.context.scene.sequence_editor.sequences_all
    depsgraph = bpy.context.evaluated_depsgraph_get()

    fps = bpy.context.scene.render.fps
    
    for sequence in sequences:

        if (sequence.type=="SOUND" and not sequence.mute):
    
            if sequence.frame_final_start < bpy.context.scene.frame_start:
                start_time = bpy.context.scene.frame_start / fps
            else:
                start_time = sequence.frame_final_start / fps
            
            if sequence.frame_final_end > bpy.context.scene.frame_end:
                end_time = bpy.context.scene.frame_end / fps
            else:
                end_time = sequence.frame_final_end / fps
              
            audio = sequence.sound.evaluated_get(depsgraph).factory
            mag = np.mean( audio.limit(start_time, end_time).data(), axis=1)
            
            sample_rate = len(mag)/(end_time - start_time)
                        
        break

    return mag, sample_rate

def avg_per_frame(array, spf, normalize=True):
    fps = bpy.context.scene.render.fps
    start_frame = bpy.context.scene.frame_start
    end_frame = bpy.context.scene.frame_end
    
    array_per_frame = np.zeros(end_frame - start_frame + 1)
    
    for i in range(len(array)):
        frame = int(i//spf)
        array_per_frame[frame] += array[i] / spf
   
    if normalize:
        array_per_frame = array_per_frame/np.linalg.norm(array_per_frame)
    
    return array_per_frame
    
def filter(seq, type, cutoff, order, nyquist):
    if type != 'bandpass':
        cutoff = cutoff/nyquist
    else:
        cutoff = [freq/nyquist for freq in cutoff]
    b, a = signal.butter(order, cutoff, type)
    filtered = signal.filtfilt(b, a, seq)
    return filtered

def move_cursor(offset):
    location = bpy.context.scene.cursor.location
    bpy.context.scene.cursor.location = location + Vector(offset)

def move_origin(offset):
    cursor_location = deepcopy(bpy.context.scene.cursor.location)
    bpy.context.scene.cursor.location =  bpy.context.object.location
    move_cursor(offset)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    bpy.context.scene.cursor.location = cursor_location
    
def init_bars(name, replace, scale=1):
    objects = bpy.context.scene.objects
    if replace and name in bpy.data.collections:
        for obj in bpy.data.collections[name].objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(bpy.data.collections[name])
    collection = bpy.data.collections.new(name=name)
    bpy.context.scene.collection.children.link(collection)
    
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.transform.translate(value=(0,0,-1.25*scale))
    bpy.ops.transform.resize(value=(4*scale,1*scale,.15*scale))
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    move_origin( (0, 0, (.15 * scale)) )
    total = bpy.context.object
    total.name = name + "_Total"
    collection.objects.link(total)
    
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.transform.resize(value=(scale,scale,.1*scale))
    bpy.ops.transform.translate(value=(3*scale,0,-.9*scale))
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    move_origin( (0, 0, -(.1 * scale)) )
    bass = bpy.context.object
    bass.name = name + "_Bass"
    collection.objects.link(bass)
    
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.transform.resize(value=(scale,scale,.1*scale))
    bpy.ops.transform.translate(value=(1*scale,0,-.9*scale))
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    move_origin( (0, 0, -(.1 * scale)) )
    lowmid = bpy.context.object
    lowmid.name = name + "_Lowmid"
    collection.objects.link(lowmid)
    
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.transform.resize(value=(scale,scale,.1*scale))
    bpy.ops.transform.translate(value=(-1*scale,0,-.9*scale))
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    move_origin( (0, 0, -(.1 * scale)) )
    mid = bpy.context.object
    mid.name = name + "_Mid"
    collection.objects.link(mid)
    
    bpy.ops.mesh.primitive_cube_add()
    bpy.ops.transform.resize(value=(scale,scale,.1*scale))
    bpy.ops.transform.translate(value=(-3*scale,0,-.9*scale))
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    move_origin( (0, 0, -(.1 * scale)) )
    highmid = bpy.context.object
    highmid.name = name + "_Highmid"
    collection.objects.link(highmid)
    
    return total, bass, lowmid, mid, highmid


""""""

class Visualize(Operator):
    bl_idname = "visual.ize"
    bl_label = "Visualize"
    bl_options = {"REGISTER", "UNDO"}
    
    def set_keyframes(self, scene):
        start = scene.frame_start
        end = scene.frame_end
        for frame in range(start, end):
            self.total_obj.scale.z = abs( self.total_per_frame[frame] * scene.volume_scale ) + scene.volume_offset
            self.total_obj.keyframe_insert(data_path="scale", frame=frame)
            
            self.bass_obj.scale.z = abs( self.bass_per_frame[frame] * scene.volume_scale ) + scene.volume_offset
            self.bass_obj.keyframe_insert(data_path="scale", frame=frame)
            
            self.lowmids_obj.scale.z = abs( self.lowmids_per_frame[frame] * scene.volume_scale ) + scene.volume_offset
            self.lowmids_obj.keyframe_insert(data_path="scale", frame=frame)
            
            self.mids_obj.scale.z = abs( self.mids_per_frame[frame] * scene.volume_scale ) + scene.volume_offset
            self.mids_obj.keyframe_insert(data_path="scale", frame=frame)
            
            self.highmids_obj.scale.z = abs( self.highmids_per_frame[frame] * scene.volume_scale ) + scene.volume_offset
            self.highmids_obj.keyframe_insert(data_path="scale", frame=frame)

    def execute(self, context):
        print("Retrieving magnitudes...")
        magnitudes, sample_rate = get_seq_magnitudes()
        nyq = .5 * sample_rate

        scene = bpy.context.scene

        fps = scene.render.fps
        spf = sample_rate / fps

        print("Filtering...")
        bass = filter(magnitudes, 'lowpass', scene.bass_cutoff, 4, nyq)
        lowmids  = filter(magnitudes, 'bandpass', [scene.bass_cutoff,  scene.lowmid_cutoff], 4, nyq)
        mids = filter(magnitudes, 'bandpass', [scene.lowmid_cutoff, scene.highmid_cutoff], 4, nyq)
        highmids = filter(magnitudes, 'highpass', scene.highmid_cutoff, 4, nyq)

        print("Compressing to frames...")
        self.total_per_frame = avg_per_frame(magnitudes, spf, scene.normalize)
        self.bass_per_frame = avg_per_frame(bass, spf, scene.normalize)
        self.lowmids_per_frame = avg_per_frame(lowmids, spf, scene.normalize)
        self.mids_per_frame = avg_per_frame(mids, spf, scene.normalize)
        self.highmids_per_frame = avg_per_frame(highmids, spf, scene.normalize)

        print("Generating visualizer objects...")

        self.total_obj, self.bass_obj, self.lowmids_obj, self.mids_obj, self.highmids_obj = init_bars(name=scene.name, 
                                                                                                    replace=scene.replace)
        
        print("Setting keyframes...")                                                                                                    
                                                                                    
        self.set_keyframes(scene)
        
        print(":D")

        return {"FINISHED"}
    
PROPS = [
    ('name', bpy.props.StringProperty(name='Name', default='')),
    ('replace', bpy.props.BoolProperty(name='Replace', default=False)),
    ('volume_scale', bpy.props.FloatProperty(name='Volume Scale', default=10)),
    ('volume_offset', bpy.props.FloatProperty(name='Volume Offset', default=.1)),
    ('bass_cutoff', bpy.props.FloatProperty(name='Bass cutoff', default=250)),
    ('lowmid_cutoff', bpy.props.FloatProperty(name='Lower-midrange cutoff', default=500)),
    ('mid_cutoff', bpy.props.FloatProperty(name='Midrange cutoff', default=2000)),
    ('highmid_cutoff', bpy.props.FloatProperty(name='Higher-midrange cutoff', default=4000)),
    ('normalize', bpy.props.BoolProperty(name='Normalize', default=True))
]

class VisualizerPanel(bpy.types.Panel):  
    
    bl_space_type = "VIEW_3D"  
    bl_region_type = "UI"  

    bl_category = "Visualizer"  
    bl_label = "Visualizer generation" 

    def draw(self, context):
        row = self.layout.row()
        row.operator("visual.ize", text="Visualize!")

        self.layout.separator()
        
        row = self.layout.row()
        row.prop(context.scene, 'name')
        row = self.layout.row()
        row.prop(context.scene, 'replace')
        row = self.layout.row()
        row.prop(context.scene, 'volume_scale')
        row = self.layout.row()
        row.prop(context.scene, 'volume_offset')

        box = self.layout.box()
        box.label(text="Frequency bins")
        row = box.row()
        row.prop(context.scene, 'bass_cutoff')
        row = box.row()
        row.prop(context.scene, 'lowmid_cutoff')
        row = box.row()
        row.prop(context.scene, 'mid_cutoff')
        row = box.row()
        row.prop(context.scene, 'highmid_cutoff')
        row = box.row()
        row.prop(context.scene, 'normalize')
                    
def register():
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.Scene, prop_name, prop_value)
    bpy.utils.register_class(VisualizerPanel)
    bpy.utils.register_class(Visualize)


def unregister():
    for (prop_name, _) in PROPS:
        delattr(bpy.types.Scene, prop_name)
    bpy.utils.unregister_class(Visualize)
    bpy.utils.unregister_class(VisualizerPanel)

register()
