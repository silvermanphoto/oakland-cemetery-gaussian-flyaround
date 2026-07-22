# -*- coding: utf-8 -*-
# build_flyover_scene_v2.py — corrected env/wire/sequencer/MRQ pass (26-029).
# Fixes over v1: robust median-of-tile-origins center (floater-immune) for the
# PlayerStart + example camera path; correct SkyLight/fog property names; clean
# LevelSequence rebuild; MRQ config now that MovieRenderPipeline is enabled.
# Idempotent, per-section guarded, writes a JSON report. ASCII only.
import unreal, json

MAP="/Game/Maps/OaklandFlyaround"; CINE_DIR="/Game/Cinematics"
SEQ_NAME="OaklandFlyover_Example"; MRQ_NAME="MRQ_Oakland_4K"
REPORT=r"C:\UE_scripts\flyover_build_report_v2.json"
SUN_PITCH,SUN_YAW,SUN_ROLL=-12.73,50.11,0.0

report={"sections":{},"notes":[]}
def sect(n,ok,d=""):
    report["sections"][n]={"ok":bool(ok),"detail":str(d)[:400]}
    unreal.log("[SECT] {0} = {1}  {2}".format(n,"OK" if ok else "FAIL",d))
def note(s): report["notes"].append(str(s)); unreal.log("[NOTE] "+str(s))

les=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les.load_level(MAP)

def find(label):
    for a in eas.get_all_level_actors():
        try:
            if a.get_actor_label()==label: return a
        except Exception: pass
    return None
def spawn_labeled(cls,label,loc=None,rot=None):
    e=find(label)
    if e is not None: return e,False
    a=eas.spawn_actor_from_class(cls,loc or unreal.Vector(0,0,0),rot or unreal.Rotator(0,0,0))
    if a is not None: a.set_actor_label(label)
    return a,True
def median(vals):
    s=sorted(vals); n=len(s); return s[n//2] if n%2 else 0.5*(s[n//2-1]+s[n//2])

# ---- robust center from 36 tile origins -------------------------------------
tiles=[a for a in eas.get_all_level_actors() if a.get_actor_label().startswith("tile_")]
oxs=[];oys=[];ozs=[]; umin=[1e18]*3; umax=[-1e18]*3
for a in tiles:
    try:
        org,ext=a.get_actor_bounds(False)
        oxs.append(org.x);oys.append(org.y);ozs.append(org.z)
        for i,(o,e) in enumerate([(org.x,ext.x),(org.y,ext.y),(org.z,ext.z)]):
            umin[i]=min(umin[i],o-e); umax[i]=max(umax[i],o+e)
    except Exception: pass
if oxs:
    center=unreal.Vector(median(oxs),median(oys),median(ozs))
else:
    center=unreal.Vector(0,0,900)
report["center_median"]=[center.x,center.y,center.z]
report["union_raw"]={"min":umin,"max":umax,"n":len(oxs)}
sect("bounds",len(oxs)==36,"center=({0:.0f},{1:.0f},{2:.0f}) from {3} tiles (union raw floater-inflated)".format(center.x,center.y,center.z,len(oxs)))
note("union raw min={0} max={1} (floaters inflate this; pawn soft-bounds use it + margin at runtime)".format(
    [int(v) for v in umin],[int(v) for v in umax]))

halfN=13000.0; halfE=9000.0
eye_z=center.z+1500.0

# ---- Sun (re-assert) --------------------------------------------------------
try:
    dl,_=spawn_labeled(unreal.DirectionalLight,"Sun_Directional",unreal.Vector(center.x,center.y,eye_z+5000),
                       unreal.Rotator(SUN_PITCH,SUN_YAW,SUN_ROLL))
    dl.set_actor_rotation(unreal.Rotator(SUN_PITCH,SUN_YAW,SUN_ROLL),False)
    lc=dl.get_component_by_class(unreal.DirectionalLightComponent)
    lc.set_editor_property("intensity",6.0); lc.set_editor_property("use_temperature",True)
    lc.set_editor_property("temperature",4600.0); lc.set_editor_property("light_source_angle",1.0)
    try: lc.set_editor_property("atmosphere_sun_light",True)
    except Exception: pass
    sect("directional_light",True,"pitch=%.2f yaw=%.2f"%(SUN_PITCH,SUN_YAW))
except Exception as e: sect("directional_light",False,e)

# ---- SkyAtmosphere ----------------------------------------------------------
try:
    sa,_=spawn_labeled(unreal.SkyAtmosphere,"SkyAtmosphere",unreal.Vector(center.x,center.y,center.z))
    sect("sky_atmosphere",sa is not None,"")
except Exception as e: sect("sky_atmosphere",False,e)

# ---- SkyLight (correct: intensity, real_time_capture) -----------------------
try:
    sl,_=spawn_labeled(unreal.SkyLight,"SkyLight",unreal.Vector(center.x,center.y,eye_z))
    slc=sl.get_component_by_class(unreal.SkyLightComponent)
    for k,v in [("real_time_capture",True),("intensity",1.0)]:
        try: slc.set_editor_property(k,v)
        except Exception as e2: note("skylight %s: %s"%(k,e2))
    sect("sky_light",True,"intensity=1.0 real_time_capture=on")
except Exception as e: sect("sky_light",False,e)

# ---- ExponentialHeightFog (correct: enable_volumetric_fog) ------------------
try:
    fog,_=spawn_labeled(unreal.ExponentialHeightFog,"HeightFog",unreal.Vector(center.x,center.y,center.z-900))
    fc=fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    for k,v in [("fog_density",0.010),("fog_height_falloff",0.12),
                ("enable_volumetric_fog",True),
                ("volumetric_fog_scattering_distribution",0.4),
                ("volumetric_fog_extinction_scale",1.0),
                ("volumetric_fog_albedo",unreal.Color(210,190,170,255))]:
        try: fc.set_editor_property(k,v)
        except Exception as e2: note("fog %s: %s"%(k,e2))
    try: fc.set_editor_property("fog_inscattering_luminance",unreal.LinearColor(0.75,0.62,0.48,1.0))
    except Exception as e2: note("fog inscattering: %s"%e2)
    sect("height_fog",True,"density=0.010 enable_volumetric_fog=on")
except Exception as e: sect("height_fog",False,e)

# ---- PostProcess (re-assert) ------------------------------------------------
try:
    ppv,_=spawn_labeled(unreal.PostProcessVolume,"PostProcess_Global",unreal.Vector(center.x,center.y,eye_z))
    ppv.set_editor_property("unbound",True); ppv.set_editor_property("priority",1.0)
    s=ppv.get_editor_property("settings")
    s.set_editor_property("override_auto_exposure_method",True)
    s.set_editor_property("auto_exposure_method",unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_auto_exposure_bias",True); s.set_editor_property("auto_exposure_bias",11.0)
    s.set_editor_property("override_motion_blur_amount",True); s.set_editor_property("motion_blur_amount",0.30)
    s.set_editor_property("override_bloom_intensity",True); s.set_editor_property("bloom_intensity",0.5)
    ppv.set_editor_property("settings",s)
    sect("post_process",True,"manual exposure, motion blur 0.30")
except Exception as e: sect("post_process",False,e)

# ---- GameMode override + PlayerStart at real center -------------------------
try:
    ues=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world=ues.get_editor_world()
    ws=world.get_world_settings()
    gm=getattr(unreal,"OaklandFlyGameMode",None)
    if gm is not None:
        ws.set_editor_property("default_game_mode",gm); sect("gamemode_override",True,"AOaklandFlyGameMode")
    else: sect("gamemode_override",False,"OaklandFlyGameMode missing")
except Exception as e: sect("gamemode_override",False,e)

try:
    ps_loc=unreal.Vector(center.x-halfN*0.9, center.y, eye_z)
    ps=find("FlyStart") or eas.spawn_actor_from_class(unreal.PlayerStart,ps_loc,unreal.Rotator(-5,0,0))
    ps.set_actor_label("FlyStart"); ps.set_actor_location(ps_loc,False,False)
    ps.set_actor_rotation(unreal.Rotator(-5.0,0.0,0.0),False)   # look +X (north, up the site)
    sect("player_start",True,"loc=({0:.0f},{1:.0f},{2:.0f}) look +X".format(ps_loc.x,ps_loc.y,ps_loc.z))
except Exception as e: sect("player_start",False,e)

# ---- Clean LevelSequence rebuild + CineCamera + 20s example path ------------
def path_points():
    x0=center.x-halfN*0.9; x1=center.x+halfN*0.5; y=center.y; z=eye_z
    return [
        (0.0, unreal.Vector(x0,        y,            z),      unreal.Rotator(-4,  0, 0)),  # gate approach, low
        (7.0, unreal.Vector(x0+halfN*0.5, y+halfE*0.3, z-350), unreal.Rotator(-3, 10, 0)),  # entering the avenue
        (14.0,unreal.Vector(center.x,  y-halfE*0.25,  z-150),  unreal.Rotator(-2, -8, 0)),  # avenue glide
        (20.0,unreal.Vector(x1,        y,            z+300),  unreal.Rotator(-1,  5, 0)),  # rise to reveal
    ]
seq=None; cine=None
try:
    if not unreal.EditorAssetLibrary.does_directory_exist(CINE_DIR):
        unreal.EditorAssetLibrary.make_directory(CINE_DIR)
    seq_path="{0}/{1}".format(CINE_DIR,SEQ_NAME)
    old=find("FlyoverCine")
    if old is not None: eas.destroy_actor(old)
    if unreal.EditorAssetLibrary.does_asset_exist(seq_path):
        unreal.EditorAssetLibrary.delete_asset(seq_path)
    seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(SEQ_NAME,CINE_DIR,unreal.LevelSequence,unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(24,1))
    seq.set_playback_start_seconds(0.0); seq.set_playback_end_seconds(20.0)

    pts=path_points()
    cine,_=spawn_labeled(unreal.CineCameraActor,"FlyoverCine",pts[0][1],pts[0][2])
    try:
        ccc=cine.get_cine_camera_component(); ccc.set_editor_property("current_focal_length",24.0)
    except Exception as e2: note("cine focal: %s"%e2)
    binding=seq.add_possessable(cine)
    tt=binding.add_track(unreal.MovieScene3DTransformTrack); ts=tt.add_section(); ts.set_range_seconds(0.0,20.0)
    chans=ts.get_all_channels()
    fr=seq.get_display_rate().numerator
    for (t,loc,rot) in pts:
        f=unreal.FrameNumber(int(round(t*fr)))
        vals=[loc.x,loc.y,loc.z,rot.roll,rot.pitch,rot.yaw,1.0,1.0,1.0]
        for i,ch in enumerate(chans):
            if i<len(vals):
                try: ch.add_key(f,float(vals[i]))
                except Exception: pass
    try:
        cut=seq.add_track(unreal.MovieSceneCameraCutTrack); cs=cut.add_section(); cs.set_range_seconds(0.0,20.0)
        try:
            bid=unreal.MovieSceneObjectBindingID(); bid.set_editor_property("guid",binding.get_id())
            cs.set_editor_property("camera_binding_id",bid)
        except Exception as eb: note("cut binding: %s"%eb)
    except Exception as ec: note("cut track: %s"%ec)
    sect("level_sequence",True,"clean rebuild, 4-key 20s path in real coords")
except Exception as e: sect("level_sequence",False,e)

# ---- MRQ config (plugin now enabled) ----------------------------------------
try:
    mrq_path="{0}/{1}".format(CINE_DIR,MRQ_NAME)
    cfg_cls=getattr(unreal,"MoviePipelinePrimaryConfig",None) or getattr(unreal,"MoviePipelineMasterConfig",None)
    if cfg_cls is None:
        sect("mrq_config",False,"MoviePipeline classes still absent (plugin load?)")
    else:
        if unreal.EditorAssetLibrary.does_asset_exist(mrq_path):
            unreal.EditorAssetLibrary.delete_asset(mrq_path)
        cfg=unreal.AssetToolsHelpers.get_asset_tools().create_asset(MRQ_NAME,CINE_DIR,cfg_cls,None)
        for cls_name,setter in [
            ("MoviePipelineOutputSetting", None),
            ("MoviePipelineAntiAliasingSetting", None),
            ("MoviePipelineDeferredPassBase", None),
            ("MoviePipelineImageSequenceOutput_PNG", None)]:
            c=getattr(unreal,cls_name,None)
            if c is None: note("mrq class missing: %s"%cls_name); continue
            try: cfg.find_or_add_setting_by_class(c)
            except Exception as e2: note("mrq add %s: %s"%(cls_name,e2))
        try:
            outp=cfg.find_setting_by_class(unreal.MoviePipelineOutputSetting)
            if outp: outp.set_editor_property("output_resolution",unreal.IntPoint(3840,2160))
        except Exception as e2: note("mrq res: %s"%e2)
        try:
            aa=cfg.find_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
            if aa:
                aa.set_editor_property("temporal_sample_count",32)
                aa.set_editor_property("spatial_sample_count",1)
        except Exception as e2: note("mrq aa: %s"%e2)
        unreal.EditorAssetLibrary.save_asset(mrq_path)
        sect("mrq_config",True,"4K, 32 temporal samples, deferred, PNG")
except Exception as e: sect("mrq_config",False,e)

# ---- save + validate + report ----------------------------------------------
try:
    les.save_current_level()
    if seq is not None: unreal.EditorAssetLibrary.save_asset("{0}/{1}".format(CINE_DIR,SEQ_NAME))
    sect("save",True,"")
except Exception as e: sect("save",False,e)
try:
    labels=[a.get_actor_label() for a in eas.get_all_level_actors()]
    want=["Sun_Directional","SkyAtmosphere","SkyLight","HeightFog","PostProcess_Global","FlyStart","FlyoverCine"]
    present={w:(w in labels) for w in want}
    report["validation"]={"present":present,"n_actors":len(labels)}
    sect("validate",all(present.values()),json.dumps(present))
except Exception as e: sect("validate",False,e)
try:
    with open(REPORT,"w") as fh: json.dump(report,fh,indent=1)
except Exception as e: unreal.log_warning("report write: %s"%e)
unreal.log("BUILD_FLYOVER_SCENE_V2_DONE")
