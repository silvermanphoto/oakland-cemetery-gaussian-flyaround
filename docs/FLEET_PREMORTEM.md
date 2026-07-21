# Fleet Pre-Mortem — adversarial sweep before scaling (Fable, 2026-07-21)

Premise: it is two days from now and the fleet phase failed or bled. What went
wrong? Each risk below carries its mitigation, now binding on the fleet driver.

## 1. Cross-lane collisions (new class — nothing so far has run 4 lanes)
- **Relay-code collision:** two lanes running runpodctl transfers concurrently
  from the same Skychief sender directory can grab each other's one-shot codes
  or stage-tars. MITIGATION: per-lane staging dirs (`_stage\lane1\`, `_stage\
  lane2\`...), per-lane code prefixes, and one transfer at a time per MACHINE
  (Skychief's uplink saturates near one relay anyway — serialize sends through
  a named queue file).
- **Skychief disk contention:** 3 pods pulling + 3090 training + pool reads.
  H: RAID handles reads; C: NVMe holds active training frames. MITIGATION:
  fleet driver checks C: free (floor 80 GB) before staging each next cell's
  frames; deletes a cell's C: frames only after its trained PLY is
  byte-verified on H:.
- **gpu_state races:** only the 3090 lane writes gpu_state.txt; cloud lanes
  never touch it. Already bounded, keep it so.

## 2. The heavier-cell VRAM cliff (the pilot's own lesson, now inverted)
tile_2_1 (318 cams) fits the 3090 so far; the pilot cell (462) OOMed. The
interior range runs to 652 cams. The cliff sits somewhere in 318..462.
MITIGATION: the 3090 lane takes cells in ASCENDING camera count and records
peak VRAM per cell; the first OOM sets the measured ceiling and every cell
above it routes to 48 GB pods. Never assume; the ceiling gets measured once
and written into the driver's routing table. Pods (48 GB) have ~2x margin at
12M native — treat pod OOM as a defect to investigate, not to retry blindly.

## 3. Frame/name mix-ups at scale (the reversed-numbering trap's big brother)
36 cells x per-cell sparse subsets x a shared pool = one wrong images.txt
poisons a 3-hour train silently (it would still converge — on the wrong
frames). MITIGATION: the fleet driver verifies per cell BEFORE launch:
(a) images.txt row count equals the manifest's camera count for that cell,
(b) 5 random stems resolve in the pool/junction, (c) the cell's points3D.txt
centroid falls inside its crop_aabb (catches sparse/cell mismatches). Three
cheap checks, every cell, logged.

## 4. Quality drift across the fleet (nobody re-judges 16 cells by eye)
A cell could finish "successfully" at visibly worse quality (bad init, a
corrupted frame subset, a loss plateau high above peers). MITIGATION: the
driver records final loss + splat count + wall-clock per cell into a fleet
ledger; any cell whose final loss sits >20% above the fleet median gets
flagged and ONE matched-view render compared against its v1 predecessor
before acceptance. Joel sees flagged cells only — machine-gate first, his
eye second (principle 7).

## 5. Long-arc watcher decay (the project's recurring wound)
Every watcher failure so far happened at stage BOUNDARIES, not mid-stage.
The fleet has ~40+ boundaries ahead. MITIGATION: the driver is a standing
QUEUE, not a chain — each lane loops: claim next cell from the queue file,
run stages, byte-verify, mark done, claim next. No hand-off exists to drop;
an idle lane with a non-empty queue is the alarm condition. lanes.json gets
one lane entry per active machine with "queue non-empty AND no progress in
45 min = ALARM"; the heartbeat enforces it every 15 minutes.

## 6. Money leaks under parallelism (3 meters instead of 1)
Three pods idle-bleed 3x faster than the audit's worst case. MITIGATION:
each pod's lane entry in lanes.json carries its id; the sentinel already
alarms on 30-min idle GPU and the $15 balance floor; the driver ALSO
terminates any pod whose queue is empty (finished cells, none remaining)
within 10 minutes — pods die when unassigned, per the standing rule. Spend
checkpoint written to the fleet ledger at every cell completion.

## 7. Assembly-phase assumptions (deferred but armed)
The 36 v2 tiles will NOT drop into the existing UE world: the combined solve
frame differs from v1's (proven on screen), so ALL 36 UE actors must be
re-imported from v2 crops in one sweep — never mixed. The UE import re-run
is a single-frame-family operation; the driver must tag every fleet PLY with
its solve generation in the filename (tile_X_Z_12M_c2.ply, c2 = combined
solve) so a mixed import is impossible to do by accident.

## 8. The Mac conductor (single point of orchestration)
Named plainly: if this Mac sleeps or the session dies, orchestration pauses
(detached trainings continue; the phone sentinel still watches meters).
MITIGATION: caffeinate armed; Joel asked to set the no-sleep toggle; every
lane's remote work is independently survivable and resumable from its
checkpoint file; the fleet queue file lives on Skychief so a fresh session
can resume the whole fleet from disk alone.

Binding: the fleet driver implements 1-6 and 8 before pod 2 opens; 7 binds
the assembly phase. This document rides in the repo; deviations need Joel.
