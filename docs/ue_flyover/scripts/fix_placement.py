# -*- coding: utf-8 -*-
# fix_placement.py — the tile floaters are PERVASIVE and sub-surface, so the
# median-of-bounds-centers Z (-6702 cm) is dragged well below ground. Horizontal
# median (X,Y) is fine (floaters are mostly vertical). Re-place the PlayerStart,
# the height-fog, and the example camera path at a proper GROUND-relative height.
# Ground in UE.Z ~= +900 cm (solve ground solveY ~= -9 m; UE.Z = -solveY*100).
import unreal, json

MAP="/Game/Maps/OaklandFlyaround"; CINE_DIR="/Game/Cinematics"; SEQ_NAME="OaklandFlyover_Example"
GROUND_Z=900.0            # UE.Z of the cemetery ground (from the solve; refine by eye)
EYE_Z=GROUND_Z+1600.0     # ~16 m above ground: a mid-canopy fly height
CX,CY=-423.0,-651.0       # horizontal centre (median of 36 tile origins; floater-robust)
halfN=13000.0; halfE=9000.0
REPORT=r"C:\UE_scripts\fix_placement_report.json"

rep={}
les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les.load_level(MAP)
def find(label):
    for a in eas.get_all_level_actors():
        try:
            if a.get_actor_label()==label: return a
        except Exception: pass
    return None

# PlayerStart -> proper height, south edge, looking north (+X)
ps=find("FlyStart")
if ps:
    loc=unreal.Vector(CX-halfN*0.9, CY, EYE_Z)
    ps.set_actor_location(loc,False,False); ps.set_actor_rotation(unreal.Rotator(-5,0,0),False)
    rep["FlyStart"]=[loc.x,loc.y,loc.z]

# HeightFog -> ground level so the fog layer sits at the ground and rises
fog=find("HeightFog")
if fog:
    fog.set_actor_location(unreal.Vector(CX,CY,GROUND_Z),False,False)
    rep["HeightFog_z"]=GROUND_Z

# Rebuild camera path at proper heights: gate approach -> avenue glide -> reveal
cine=find("FlyoverCine")
seq_path="{0}/{1}".format(CINE_DIR,SEQ_NAME)
if cine and unreal.EditorAssetLibrary.does_asset_exist(seq_path):
    x0=CX-halfN*0.9; x1=CX+halfN*0.5; y=CY
    pts=[
        (0.0, unreal.Vector(x0,        y,           EYE_Z-200), unreal.Rotator(-4,  0,0)),
        (7.0, unreal.Vector(x0+halfN*0.5, y+halfE*0.3, EYE_Z-500), unreal.Rotator(-3, 10,0)),
        (14.0,unreal.Vector(CX,        y-halfE*0.25, EYE_Z-350), unreal.Rotator(-2, -8,0)),
        (20.0,unreal.Vector(x1,        y,           EYE_Z+900), unreal.Rotator( 2,  5,0)),
    ]
    cine.set_actor_location(pts[0][1],False,False); cine.set_actor_rotation(pts[0][2],False)
    seq=unreal.EditorAssetLibrary.load_asset(seq_path)
    # find the camera's transform section and re-key
    rebuilt=False
    for binding in seq.get_bindings():
        for track in binding.get_tracks():
            if isinstance(track, unreal.MovieScene3DTransformTrack):
                for sec in track.get_sections():
                    chans=sec.get_all_channels()
                    # clear existing keys then re-add
                    for ch in chans:
                        try:
                            for k in list(ch.get_keys()): ch.remove_key(k)
                        except Exception: pass
                    fr=seq.get_display_rate().numerator
                    for (t,loc,rot) in pts:
                        f=unreal.FrameNumber(int(round(t*fr)))
                        vals=[loc.x,loc.y,loc.z,rot.roll,rot.pitch,rot.yaw,1.0,1.0,1.0]
                        for i,ch in enumerate(chans):
                            if i<len(vals):
                                try: ch.add_key(f,float(vals[i]))
                                except Exception: pass
                    rebuilt=True
    rep["path_rebuilt"]=rebuilt
    unreal.EditorAssetLibrary.save_asset(seq_path)

les.save_current_level()
with open(REPORT,"w") as fh: json.dump(rep,fh,indent=1)
unreal.log("FIX_PLACEMENT_DONE "+json.dumps(rep))
