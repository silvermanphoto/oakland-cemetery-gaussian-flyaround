# Oakland Flyover — build status (Phases D + E + F prep)

**Built headless on the existing 36-tile v1 world, 2026-07-21.**
Project: `H:\2026 Files\26-029 UE\OaklandFlyaround\OaklandFlyaround.uproject` (UE 5.8, Skychief).
Everything here lives *above* the tiles — a later v2 tile swap re-runs the tile import and
nothing in this document changes. Nothing was committed to git.

---

## What exists now (asset by asset)

**Fly camera (C++, compiled into the editor — biggest risk, cleared first):**
- `AOaklandFlyPawn` — a smooth spectator-style flying camera: real inertia (ease-in / ease-out
  through a FloatingPawnMovement component), a scroll-wheel speed ramp, hold-Shift boost, subtle
  banked turns, collision fully off (pure flight), and **soft world bounds that auto-fit the splat
  volume at play** so the camera can't wander off into the void. Input (WASD + mouse-look + wheel)
  is read straight from the controller each tick, so the pawn needs no extra input setup to work.
- `AOaklandFlyGameMode` — makes that pawn the default; set as the map's GameMode Override, so
  pressing Play (or a packaged build) drops you straight into the fly camera.
- Source (reference copies): `docs/ue_flyover/scripts/OaklandFlyPawn.h` / `.cpp` /
  `OaklandFlyGameMode.h` / `.cpp`. The live source-of-truth is in the UE project's
  `Source/OaklandFlyaround/` on Skychief.

**Environment + lighting (Phase D) — the surround the engine lights around the pre-lit splats:**
- `Sun_Directional` — a DirectionalLight aimed to match the capture's real sun (see below), warm
  (4600 K), acting as the sky's sun.
- `SkyAtmosphere` — physically-based sky.
- `SkyLight` — real-time sky ambient fill.
- `HeightFog` — ExponentialHeightFog at ground level with subtle **volumetric fog** on, warm tint,
  low density — the soft banks of light between the trees.
- `PostProcess_Global` — an unbound PostProcessVolume: filmic tonemap (UE default), **manual
  exposure** (no auto-brightness pumping), gentle bloom, and **motion blur** for the reel.

**Sequencer scaffold (Phase F prep):**
- `LevelSequence` `/Game/Cinematics/OaklandFlyover_Example` — 24 fps, 20 seconds, with a bound
  `FlyoverCine` CineCameraActor (24 mm) and a 4-key placeholder path (gate approach → avenue glide
  → reveal) plus a camera-cut track. This is a scaffold for Joel to author over, not a finished shot.
- `PlayerStart` `FlyStart` — placed **inside** the scene on the south edge at ~16 m height looking
  north across the cemetery (so Play starts inside the sweet spot, not outside looking at a haze-ball).

---

## The sun assumption (corrected — this was NOT a 10 a.m. morning capture)

The task brief assumed a ~10 a.m. December morning. The source frames say otherwise:

- The DJI filenames + EXIF `DateTimeOriginal` put the flight at **15:36:57 → 16:52:49 on
  Dec 22, 2022** — a **late-afternoon** capture (Windows independently reads "Date taken 3:36 PM").
  Atlanta is EST (no DST in December); the drone GPS confirms Atlanta. 15:36 UTC would have been
  10:36 EST, which is why the timezone was pinned two independent ways before trusting it.
- NOAA solar position for that window (lat 33.75, lon −84.37): the sun tracked **southwest, low
  and descending** — start az 223°/el 18.5°, **midpoint az 230°/el 12.7°**, end az 236°/el 6.4°
  (consistent with the ~5:33 p.m. Atlanta sunset that day).
- The baked light is the ~76-minute average, so the single-sun match is the **midpoint: az ≈ 230°,
  el ≈ 13°**. Georegistration (`docs/boundary_cut/georegistration_transform.json`, rotation
  −0.002°) plus the NanoGS import axis bake gives **UE world +X = North, +Y = East, +Z = Up**, so
  the DirectionalLight rotation is **Pitch −12.73°, Yaw +50.11°, Roll 0** (light travels
  north-east and downward; sun sits south-west and low). Warm winter afternoon.
- **One soft assumption remains:** the drone's camera clock accuracy (this DJI unit stored no GPS
  time field to cross-check to the second). The direction is high-confidence; Joel should eye-check
  it against a shadow in the splats and nudge the yaw a few degrees if needed (one number, one file).

---

## Fly-pawn tunables (Joel's one-file taste pass)

Every feel value is a default in **one file** — `Source/OaklandFlyaround/OaklandFlyPawn.h` (edit +
recompile), or override per-instance in a Blueprint child.

| Feel parameter | Default | What it does | Turn it... |
|---|---|---|---|
| CruiseSpeed | 1200 cm/s | Base flight speed the scroll wheel ramps | up = faster cruise |
| SpeedMin / SpeedMax | 150 / 12000 cm/s | Clamps for the scroll-wheel ramp | widen for more range |
| ScrollSpeedStep | 1.15× | Speed multiplier per wheel notch | up = coarser ramp |
| BoostMultiplier | 3.0× | Hold-Shift sprint multiplier | up = faster sprint |
| Acceleration | 2400 cm/s² | Ease-IN — how fast it reaches speed | down = floatier launch |
| Deceleration | 2400 cm/s² | Ease-OUT — glide when you release | down = longer glide |
| LookSensitivity | 1.0 °/count | Mouse-look speed | up = twitchier |
| LookSmoothing | 12.0 | Look damping (higher = crisper) | down = silkier/laggier |
| bInvertPitch | false | Invert vertical mouse | — |
| bRequireRMBToLook | true | Hold Right-Mouse to look+fly (UE-editor grammar) | false = always-look |
| bEnableBanking | true | Subtle camera roll into turns | false = none |
| MaxBankAngle | 8° | Max roll into a hard turn | up = more dramatic |
| BankInterpSpeed | 3.0 | How fast the bank eases in/out | — |
| bAutoComputeBounds | true | Confine camera to the splat volume (v2-proof) | false = manual box |
| BoundsMarginCm | 6000 (60 m) | Horizontal breathing room past the splats | up = roam farther |
| BoundsVerticalMarginCm | 12000 (120 m) | Head / floor room | — |
| BoundsPushStrength | 3.0 | How firmly the soft wall eases you back | up = firmer wall |

Movement keys: **W/S** forward-back · **A/D** strafe · **E / Space** up · **Q / Ctrl** down ·
**scroll** = speed · **Shift** = boost. Hold **Right-Mouse** to look and fly.

---

## Headless render outcome

*(finalized below once the render resolves — see the render section)*

---

## What still needs eyes-on (interactive session)

1. **Visual seam / composition check + feel pass.** Fly it in PIE: confirm the 36 tiles seam
   invisibly, the sun direction matches the shadows baked in the splats (nudge yaw if needed), the
   fog/exposure read well against the pre-lit splats, and the pawn feel (accel, damping, look,
   speed range) is to taste. All feel numbers are one file (above).
2. **MRQ config asset.** Deferred: enabling the MovieRenderPipeline plugin headless crashed the
   editor at launch because this source-engine build lacks the OpenColorIO module MRP depends on.
   In the GUI, enable **Movie Render Queue** via the Plugins browser (it offers to build the missing
   modules), then create `MRQ_Oakland_4K` (4K, 32 temporal samples, deferred pass, PNG) — ~1 minute.
3. **Author the real reel path** over the placeholder `OaklandFlyover_Example` sequence (Phase F proper).

## What needs nothing when the v2 tiles land

**Confirmed: nothing structural.** The environment, lighting, fly pawn, GameMode, PlayerStart, and
Sequencer all sit above the tiles and reference no tile by name. The v2 swap is just a re-run of the
tile import; the pawn's soft bounds even re-fit the new splat volume automatically at play. The one
thing worth a glance after v2: the sun *yaw* (a creative shadow match) and the PlayerStart height,
both single numbers.
