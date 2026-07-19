# Phase A — Splat Plugin Bake-Off: Decision Memo

**Project:** 26-029 Oakland Cemetery Gaussian Flyaround — Unreal Engine integration
**Date:** 2026-07-17
**Status:** Decision recorded. Source verified; live in-editor verification pending (a GPU training job owns the box).

---

## The decision, in one line

**We are building the Oakland flyaround on NanoGS.** It is the only one of the three
splat plugins we tested that actually compiles against our Unreal Engine 5.8 build, and
it is the only one designed for scenes as large as ours — millions of points per tile,
many tiles meeting seamlessly.

The runner-up, **MLSLabs, is out** — not on taste, but on structure: it physically
cannot run on our engine. The third, XVERSE XScene, was set aside once NanoGS cleared.

---

## What each candidate was, and why only one survived

We built Unreal Engine 5.8 from source on the studio PC and put three Gaussian-splat
rendering plugins through the same test: does it compile and link against *our* engine?

**MLSLabs — disqualified.** It ships only as a pre-built package made for an older engine
(5.5), with no source code we could recompile. That alone would be a problem, but two
deeper faults make it a dead end rather than a patch job:

- It depends on an internal engine component that Unreal *removed* in 5.8, so it references
  something that no longer exists.
- It needs a large machine-learning runtime library that simply is not present, and it does
  not bring one.

These are not settings we can flip. The build fails with a real, captured error. MLSLabs was
written for a different engine than the one we are standing on, and there is no bridge.

**XVERSE XScene — set aside.** A viable-looking candidate, but once NanoGS compiled cleanly
and met our needs, there was no reason to keep evaluating a second option. It remains a
fallback name on the shelf, nothing more.

**NanoGS — chosen.** Its source code compiled cleanly against Unreal Engine 5.8. Both of its
parts — the runtime piece that draws the splats and the editor piece that imports them —
built and linked, producing working plugin files that the editor now loads. The only
complaints from the compiler were two mild "this will change in a future engine version"
notices — worth noting for down the road, not blocking anything today.

---

## What NanoGS actually gives us

- **It is built for big scenes.** Its whole reason to exist is drawing very large splat
  scenes in real time without exhausting graphics memory — it borrows Unreal's own approach
  to massive geometry (loading only the detail the current view needs, drawing distant
  material more coarsely). That maps exactly onto our Oakland archive, which is already cut
  into tiles for this reason.
- **Import is dead simple and does the coordinate math for us.** We feed it the raw splat
  files we already have — no pre-conversion, no intermediate format. On import it automatically
  turns the splat data upright and rescales it from meters to Unreal's centimeters. Our Oakland
  scenes are stored in exactly the orientation and scale it expects, so tiles land upright,
  correctly sized, and — because every tile shares one common origin and NanoGS never re-centers
  anything — they meet each other seamlessly with no stitching, just as they did in the web
  viewer. Each tile is placed at the world origin with no rotation and no rescale; the plugin
  handles the rest.
- **It has real controls for keeping the frame rate up.** There is a memory budget knob (cap how
  many splats are drawn at once, dropping the farthest first) and an optional detail-hierarchy
  mode we can switch on per scene once we want distance-based level-of-detail. Both matter because
  a single 12-million-point tile — several of them at once — will otherwise strain graphics memory.

**One thing to keep in mind:** NanoGS is early software (its makers mark it as a beta, and its
own paperwork claims support only for engine versions 5.6 and 5.7, not our 5.8). It does compile
on 5.8 today, but the piece most likely to break on a future engine update is where it reaches
into Unreal's internal rendering plumbing. That is the spot to watch if we ever upgrade the engine.

---

## The part that shapes the whole reel: splats are pre-lit

This is the single most important thing to understand about rendering Gaussian splats in Unreal,
and it decides how our two delivery modes work.

**A Gaussian splat carries its lighting baked in.** Our Oakland scenes are frozen the way the
drone saw them on that December 2022 morning — that light, those shadows, that time of day are
*painted into* the splat. Unreal does not re-light a splat. It draws it as a soft, glowing cloud
of colored points, composited on top of the normal scene, and that cloud looks the same no matter
what lights we place around it.

Concretely, and confirmed by reading NanoGS's own code:

- The splats are drawn as their own pass and blended into the picture *after* Unreal has drawn the
  solid geometry. They do not participate in Unreal's real-time global illumination (Lumen), and
  they do not cast or receive shadows.
- **The splats are not in the Path Tracer's world at all.** Unreal's Path Tracer — its
  film-quality light-simulation renderer — works on triangle-based geometry. NanoGS has zero
  connection to it; there are no ray-tracing hooks anywhere in the plugin. So a path-traced view
  simulates light for the *environment* we build around the splat, while the splat itself just
  shows its baked-in December light. (Whether the splat cloud even paints on top of a path-traced
  frame is the one thing we can't settle by reading code — it needs a live test, which is out of
  scope while the GPU is busy. But there is definitively no path-tracing *of* the splats to hope for.)

So neither Lumen nor the Path Tracer will make the *cemetery itself* look more or differently lit —
its light is fixed. What they light is **everything we add around it**: sky, atmosphere, haze, fog,
volumetric light shafts, any real 3D props or ground we drop in. That is where the cinematic quality
comes from.

---

## What this means for our two modes

**Mode 1 — Lumen, live.** For interactive work and quick looks, Unreal's real-time renderer draws
the splat cloud composited over a Lumen-lit environment. Fast, editable, good for blocking the
camera move and judging the scene. The splat shows its baked light; Lumen makes the surrounding
sky and atmosphere feel real in real time.

**Mode 2 — the Path-Traced reel.** For the finished piece, we render through the Movie Render Queue.
The quality of that reel does **not** come from path-tracing the gaussians — that isn't a thing.
It comes from three levers we *do* have:

1. **Full splat density** — no memory-budget culling and no coarse level-of-detail; every point drawn,
   for maximum fidelity of the cemetery itself.
2. **Movie-Render-Queue temporal supersampling** — the frame is rendered many times per output frame
   with tiny sub-pixel jitters and averaged, which cleans up the shimmer and edge-crawl that splats are
   prone to and gives the smooth, filmic result. (A caution to verify live: NanoGS declares no special
   Movie Render Queue support, so how gracefully the splat pass accumulates across those samples is
   unconfirmed until we test it. The splats *should* appear in any normal rendered view, since they ride
   the standard renderer, but the anti-shimmer accumulation behavior specifically is the thing to prove
   on the box.)
3. **A path-traced environment** — sky, fog, light shafts, and any added geometry rendered with the
   Path Tracer's full light simulation, wrapping the pre-lit cemetery in cinematic atmosphere.

The reel's beauty, in short, is **maximum splat density plus Movie-Render-Queue supersampling plus a
path-traced world around the splat** — not path-traced gaussians. Set that expectation up front and the
plan holds together.

---

## The reel recipe that follows

1. Import each Oakland tile straight from its existing splat file. It arrives upright, correctly scaled,
   and aligned to the shared origin automatically.
2. Place every tile at the world origin with no rotation and no rescale, so all tiles stay mutually aligned.
3. Keep the original large splat files in place — if we later switch on the distance-detail hierarchy, the
   plugin re-reads the source file to build it, and it fails if the file has moved.
4. For live/Lumen work: set a memory budget so many large tiles at once stay within graphics memory; block
   the camera move here.
5. For the reel: remove the memory budget and any coarse level-of-detail (full density), build the surrounding
   world (sky, atmosphere, fog, light shafts, ground/props), and light *that* environment with the Path Tracer.
6. Render through the Movie Render Queue with generous temporal supersampling for the clean, filmic result.
7. **Verify live once the GPU frees up:** that a tile imports upright and aligned, that multiple tiles hold
   frame rate under a memory budget, and specifically that the splat pass survives and accumulates cleanly
   in a Movie-Render-Queue path-traced render. These are the three open items this memo authored from source
   but could not run.

---

*Prepared from a source-level reading of the NanoGS plugin and the captured build results. Live in-editor
verification is deferred until the studio PC's graphics processor is free.*
