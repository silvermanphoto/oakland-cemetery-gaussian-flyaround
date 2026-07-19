# -*- coding: utf-8 -*-
# =============================================================================
#  ue_import_tiles.py  —  Oakland Cemetery dense splat tiles -> OaklandFlyaround
#  Project 26-029 (UE 5.8, NanoGS plugin).  AUTHORED 2026-07-17, NOT YET RUN.
# -----------------------------------------------------------------------------
#  WHAT THIS DOES
#    Imports each CROPPED per-tile Gaussian-splat PLY (H:\...\deliver\ue_tiles\
#    <tile>.ply — produced by export_ue_tiles.ps1) as a NanoGS
#    UGaussianSplatAsset, then drops one AGaussianSplatActor per tile into the
#    CURRENT level, each at UE world origin with an IDENTITY transform.  Every
#    tile came out of ONE shared metric solve and was cropped to its own
#    non-overlapping grid cell, so identity placement makes all tiles meet
#    seamlessly, with NO double-coverage at seams and zero hand-stitching
#    (verified live 2026-07-17 — see COORDINATE NOTE).
#
#  HOW TO RUN (pick one — this file runs NOTHING on its own):
#    A) Editor Python console  (RECOMMENDED, and the surface actually verified
#       against the source):  open OaklandFlyaround.uproject in UnrealEditor,
#       open the level you want the tiles in, then in the Output Log's Cmd
#       (set to "Python") or Tools > Execute Python Script, run this file.
#         >>> exec(open(r"H:\path\to\ue_import_tiles.py").read())
#    B) Headless-ish commandlet:
#         UnrealEditor-Cmd.exe "H:\2026 Files\26-029 UE\OaklandFlyaround\OaklandFlyaround.uproject" ^
#           -run=pythonscript -script="H:\path\to\ue_import_tiles.py"
#       NOTE: actor placement needs a loaded map.  Under -run=pythonscript no
#       map is open by default, so either (i) prefer surface A, or (ii) set
#       OPEN_MAP below to the map to load first.  See ASSUMPTION #5.
#
#  HARD PREREQUISITE (do NOT run before this is true):
#    A live GPU training job is running on Skychief as of authoring, AND the
#    cropped tiles must already exist in deliver\ue_tiles (run
#    export_ue_tiles.ps1 first — that step is CPU-only).  Importing tens of GB of
#    cropped PLY into .uasset is disk/CPU/VRAM heavy and opens the editor — run
#    ONLY once the box is free.  Live in-editor verification of this script is
#    explicitly pending (GPU-gated); it is authored for correctness against the
#    NanoGS source, not yet executed.  (Task boundary, 2026-07-17.)
#
# =============================================================================
#  COORDINATE / SCALE OWNERSHIP  (source-verified — IDENTICAL block in
#  export_ue_tiles.ps1; this is why this script applies NO transform of its own)
# -----------------------------------------------------------------------------
#  NanoGS's PLY importer BAKES BOTH conversions AT IMPORT TIME, once per splat,
#  and does NO recentering.  Verified against source (PLYFileReader.cpp:341-373,
#  431-434):
#
#    * AXIS  (COLMAP y-down -> UE z-up):  the reader hardcodes
#          UE.X =  PLY.Z * 100
#          UE.Y =  PLY.X * 100
#          UE.Z = -PLY.Y * 100        (Y negated because PLY Y points down)
#      Our Oakland global frame IS COLMAP up = -Y (gravity +Y, ground y~=-9),
#      which is exactly the reader's assumption, so tiles import UPRIGHT.
#      => We must NOT pre-rotate.  Actor rotation = IDENTITY (0,0,0).
#         Pre-applying a rotation here would DOUBLE-apply and corrupt the scene.
#
#    * SCALE (meters -> centimeters):  positions x100 (MetersToUE=100.0) and
#      scales exp-decoded then x100 are BAKED into the reader.  Our frame is
#      ~1 unit ~= 1 meter, so this is already correct.
#      => We must NOT apply any extra scale.  Actor scale = (1,1,1).
#         (This is why the superspl.at web hacks -s 0.05 / pivot-to-origin are
#          deliberately NOT used — those were web-viewer workarounds; UE gets the
#          TRUE metric frame with one shared origin.)
#
#    The old "NanoGS converts at render time / the metre->cm scale comes from the
#    actor Transform" story was WRONG: the axis flip AND the x100 scale are
#    IMPORT-TIME bakes, and the actor Transform is identity BECAUSE of that.
#
#    * SHARED ORIGIN + CROP-ONLY EXPORT:  the PC-side export does ONLY a metric-
#      frame CROP — each tile is box-filtered to its non-overlapping grid cell
#      (no rotation, no scale, no translate, no pivot).  A crop MOVES nothing: it
#      deletes the ~20% training apron so tiles no longer double-cover their
#      seams, while every kept gaussian keeps its true world position.  The import
#      likewise shifts NO positions (CalculateBounds only grows a bbox), so all
#      tiles keep ONE shared origin.  Verified live 2026-07-17: each tile's
#      gaussian centroid maps 1:1 to a distinct grid cell, and cropped tiles land
#      exactly inside their cell (e.g. cell x=2 -> x[-95.7..-11.6], cell x=3 ->
#      x[-11.6..81.2], meeting at the shared edge -11.6 with no overlap).  Placing
#      EVERY tile actor at world origin with identity keeps that shared frame
#      intact => seamless, non-overlapping seams.
#
#  DO NOT use tiles6\<tile>\crop_aabb.json for actor PLACEMENT.  Cells are used at
#  CROP time (export, by gaussian centroid), never as per-tile placement offsets;
#  every cropped PLY carries its own true world positions, so placement is
#  identity.  (The out8k tile NAME does not map to grid position either — the
#  export derives each tile's cell from its centroid, not its name.)
#
#  NO PRE-CONVERSION STEP EXISTS OR IS NEEDED.  Per the API `importMethod`, the
#  .uasset IS the converted form; feed the raw standard 3DGS binary-LE PLY
#  straight into the factory.  (Our tiles: binary_little_endian, all-float,
#  62 props incl. x,y,z,nx,ny,nz,f_dc_*,f_rest_0..44,opacity,scale_0..2,
#  rot_0..3 — SH degree 3; qualifies.)
# =============================================================================

import os
import glob
import unreal

# -----------------------------------------------------------------------------
#  CONFIG  (edit here)
# -----------------------------------------------------------------------------
# Root that holds one CROPPED PLY per tile, named <tile>.ply (the cell-cropped,
# non-overlapping tiles produced by export_ue_tiles.ps1). NOT the raw out8k tiles.
TILE_ROOT = r"H:\2026 Files\26-002 Oakland Cemetery Splat\deliver\ue_tiles"

# Where the imported .uasset tiles land in the project's content tree.
DEST_PATH = "/Game/OaklandTiles"

# Commandlet surface only (option B above): map to open before placing actors.
# Leave "" when running from the editor console with a level already open.
OPEN_MAP = ""   # e.g. "/Game/Maps/OaklandFlyaround"

# ---- TILE LIST: data-driven, swap-ready for the full 36-tile set ----
# Default = auto-discover every <tile>.ply directly under TILE_ROOT.  The export
# writes one cropped PLY per settled tile, so this SAME glob picks up all 36
# tiles automatically as they finish (11 present at authoring) — no edit required.
#
# To PIN an explicit set instead (full control / reproducibility), set
# TILES to a { asset_name : ply_path } dict and it overrides discovery.
# One-line swap example for the finished 6x6 grid:
#   TILES = { "tile_%d_%d" % (r, c):
#             os.path.join(TILE_ROOT, "tile_%d_%d.ply" % (r, c))
#             for r in range(6) for c in range(6) }
TILES = None   # None => auto-discover (see discover_tiles)


def discover_tiles():
    """Return { asset_name : ply_path } for every <tile>.ply under TILE_ROOT.
    asset_name is the PLY basename sans extension (e.g. 'tile_1_0')."""
    found = {}
    pattern = os.path.join(TILE_ROOT, "*.ply")
    for p in sorted(glob.glob(pattern)):
        name = os.path.splitext(os.path.basename(p))[0]
        found[name] = p
    return found


# -----------------------------------------------------------------------------
#  IMPORT  —  API field `importMethod`
#    Standard editor Content-Browser IMPORT factory (UGaussianSplatAssetFactory,
#    a UFactory auto-discovered by reflection).  No console command / commandlet
#    / utility-widget importer exists in source — this is the ONLY import path.
#    Python: unreal.AssetImportTask + task.factory = GaussianSplatAssetFactory()
#    driven by AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]).
# -----------------------------------------------------------------------------
def import_tile(asset_name, ply_path):
    """Import one PLY as a UGaussianSplatAsset (idempotent). Return the asset or None."""
    asset_path = "{0}/{1}".format(DEST_PATH, asset_name)

    # Idempotent: skip re-import if the .uasset already exists.
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.log("  [skip-import] asset already exists: {0}".format(asset_path))
        return unreal.EditorAssetLibrary.load_asset(asset_path)

    if not os.path.isfile(ply_path):
        unreal.log_warning("  [missing] PLY not found: {0}".format(ply_path))
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", ply_path)             # API importMethod: task.filename = the PLY
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", asset_name)
    # API importMethod: task.factory = unreal.GaussianSplatAssetFactory().
    # The factory declares Formats "ply", bEditorImport=true, SupportedClass=
    # UGaussianSplatAsset; import_asset_tasks routes to FactoryCreateFile ->
    # ImportPLYFile -> UGaussianSplatAsset::InitializeFromSplatData.
    task.set_editor_property("factory", unreal.GaussianSplatAssetFactory())
    task.set_editor_property("automated", True)                # no modal dialogs (batch)
    task.set_editor_property("replace_existing", False)        # covered by does_asset_exist above
    task.set_editor_property("save", True)                     # persist the .uasset to disk

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    # imported_object_paths is populated by the import task on success.
    out_paths = task.get_editor_property("imported_object_paths")
    if out_paths and len(out_paths) > 0:
        asset = unreal.EditorAssetLibrary.load_asset(out_paths[0])
        # Report the converted splat count as concrete evidence of a good import.
        try:
            n = asset.get_splat_count() if hasattr(asset, "get_splat_count") else "?"
        except Exception:
            n = "?"
        unreal.log("  [import OK] {0}  ({1} splats)".format(out_paths[0], n))
        return asset

    unreal.log_warning("  [import FAIL] no asset produced for {0}".format(ply_path))
    return None


# -----------------------------------------------------------------------------
#  PLACE  —  API field `placementActor`
#    Spawn AGaussianSplatActor (its RootComponent is a UGaussianSplatComponent
#    default subobject), then component.SetSplatAsset(asset) — the exact path
#    the drag-drop UActorFactoryGaussianSplat itself uses in PostSpawnActor.
#    CRITICAL: spawn at world origin with an EXPLICIT IDENTITY transform.  We do
#    NOT rely on drag-drop placement, whose factory sets bUseSurfaceOrientation
#    =true (would rotate the actor to a hit-surface normal).
# -----------------------------------------------------------------------------
def place_tile(asset_name, asset, editor_actor_sys):
    """Spawn one AGaussianSplatActor at origin/identity for `asset` (idempotent)."""
    if asset is None:
        return None

    # Idempotent: don't double-place a tile already in the level (by label).
    for a in editor_actor_sys.get_all_level_actors():
        if isinstance(a, unreal.GaussianSplatActor) and a.get_actor_label() == asset_name:
            unreal.log("  [skip-place] actor already in level: {0}".format(asset_name))
            return a

    # Identity transform: origin, zero rotation, unit scale.  See COORDINATE NOTE
    # — the metric-frame + upright + cm conversion is already baked in at import,
    # so any non-identity here would MIS-place the tile relative to its siblings.
    loc = unreal.Vector(0.0, 0.0, 0.0)
    rot = unreal.Rotator(0.0, 0.0, 0.0)

    # API placementActor: EditorActorSubsystem.spawn_actor_from_class(
    #   unreal.GaussianSplatActor, location, rotation).
    actor = editor_actor_sys.spawn_actor_from_class(unreal.GaussianSplatActor, loc, rot)
    if actor is None:
        # See ASSUMPTION #1 (NotPlaceable + programmatic spawn).
        unreal.log_warning("  [place FAIL] spawn returned None for {0}".format(asset_name))
        return None

    actor.set_actor_label(asset_name)
    # Belt-and-suspenders: force unit scale in case of any spawn default.
    actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))

    # API placementActor: actor.gaussian_splat_component (UPROPERTY
    # GaussianSplatComponent -> UE Python snake_case) .set_splat_asset(asset)
    # (UFUNCTION BlueprintCallable SetSplatAsset).  Verified in source.
    comp = actor.gaussian_splat_component
    comp.set_splat_asset(asset)

    unreal.log("  [place OK] {0} at origin/identity".format(asset_name))
    return actor


# -----------------------------------------------------------------------------
#  MAIN
# -----------------------------------------------------------------------------
def main():
    tiles = TILES if TILES else discover_tiles()
    if not tiles:
        unreal.log_error("No tiles found under {0} (glob *.ply). Run export_ue_tiles.ps1 first. Nothing to do.".format(TILE_ROOT))
        return

    unreal.log("=" * 70)
    unreal.log("NanoGS tile import — {0} tile(s) from {1}".format(len(tiles), TILE_ROOT))
    unreal.log("Destination: {0}   (identity placement, one shared solve)".format(DEST_PATH))
    unreal.log("=" * 70)

    # Commandlet surface only: open a map so actors have a level to land in.
    if OPEN_MAP:
        unreal.log("Loading map: {0}".format(OPEN_MAP))
        unreal.EditorLoadingAndSavingUtils.load_map(OPEN_MAP)

    editor_actor_sys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    imported, placed, skipped = 0, 0, 0
    for asset_name in sorted(tiles.keys()):
        ply_path = tiles[asset_name]
        unreal.log("- {0}".format(asset_name))
        existed = unreal.EditorAssetLibrary.does_asset_exist("{0}/{1}".format(DEST_PATH, asset_name))
        asset = import_tile(asset_name, ply_path)
        if asset is None:
            continue
        imported += (0 if existed else 1)
        skipped += (1 if existed else 0)
        if place_tile(asset_name, asset, editor_actor_sys):
            placed += 1

    # Persist the level so the placed actors survive editor restart.
    try:
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        les.save_current_level()
        unreal.log("Saved current level.")
    except Exception as e:
        unreal.log_warning("Could not auto-save level ({0}). Save manually (Ctrl+S).".format(e))

    unreal.log("=" * 70)
    unreal.log("DONE.  imported(new)={0}  reused(existing)={1}  placed={2}  total_tiles={3}".format(
        imported, skipped, placed, len(tiles)))
    unreal.log("=" * 70)

    # -------------------------------------------------------------------------
    #  VRAM / LOD FOLLOW-UP  (NOT executed here — see README + API knownLimits)
    #  Even after cropping, 36 tiles at a few M gaussians each (~150M+ splats
    #  total) FAR exceed VRAM.  Before viewing the full scene:
    #    * cap rendered splats:  console  ->  gs.MaxRenderBudget <N>
    #      (~195 MB working buffers per 3M budget; 0 = unlimited).
    #    * and/or enable per-asset Nanite LOD via Content Browser >
    #      Asset Actions > Nanite > Enable (re-reads the source PLY, so KEEP the
    #      cropped deliver\ue_tiles PLYs in place until Nanite is built —
    #      knownLimits).
    #  Left as an explicit manual/next step to avoid an unverified console-context
    #  call from a commandlet (ASSUMPTION #6).
    # -------------------------------------------------------------------------


if __name__ == "__main__":
    main()
else:
    # exec(open(...).read()) from the Python console lands here too.
    main()
