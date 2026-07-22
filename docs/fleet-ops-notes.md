# Fleet Ops Notes

Running record of fleet-launch operational findings that bind future launches.
The canonical live ledger + ADVANCE_PROCEDURE.txt live on Skychief
(`C:\LidargraphCapture\status\`); entries here are the Mac-side record and the
staging area for Skychief updates when the PC is reachable.

---

## 2026-07-21 — Twin pod trainer crash: the 32 GB arena wall (NOT a card-size OOM)

**What happened.** Two 48 GB cloud lanes crashed identically mid-train:
- Lane 1 (A6000 48 GB, pod `v6e0szp7n6odbz`): `tile_2_1` (318 cams) died at iter **11,968**.
- Lane 3 (A40 48 GB, pod `a6x3d2clt1ziqy`): `tile_2_2` (382 cams) died at iter **7,965**.

Both threw the same signature:
`CUDA call failed: FastGS sort-buffer allocation at .../fastgs/rasterization/src/forward.cu:60`,
then a cascade `parallel_for failed: cudaErrorInvalidDevice: invalid device ordinal`
on the recovery save (sticky-error cascade, not the real cause).

**Root cause — an artificial ceiling, not the card.** The LichtFeld build's CUDA
memory arena reserves a **hardcoded 32 GB virtual** address space regardless of the
physical card:
```
memory_arena.cu: Arena config: virtual=32 GB, initial=128 MB, max=<phys> GB
```
- A6000 (48 GB): `virtual=32, max=47`
- A40 (45 GB): `virtual=32, max=44`
- Upstream issue #792's **H200 (141 GB)**: still `virtual=32`.

`max` scales with the card; `virtual` never does. The FastGS forward-pass sort
buffer (a large transient CUB radix-sort workspace sized by gaussian-tile
intersection count at **native 8192 / 12M cap**) needs a block that pushes the
arena past its 32 GB reservation, and the allocation fails even though **28+ GB of
the card sits idle**. Lane 1's arena peaked at 19,143 MB (95.8% of committed);
lane 3 at 17,197 MB (94.1%). `tile_1_2` (410 cams — MORE cams) had trained clean on
the same lane-1 card earlier, because its transient peak stayed under 32 GB. So the
crash is driven by a cell's per-view densification/geometry, not its camera count.

**This overturns FLEET_PREMORTEM #2's "48 GB pods have ~2x margin at 12M native."**
The usable ceiling for the FastGS sort buffer is the **hardcoded 32 GB arena**, not
the card's physical VRAM. Some native-8192/12M cells cross it; a bigger card does
NOT raise it.

**There is NO memory-configuration fix in this build (validated 3 ways).**
1. Full `--help`: no arena/vmm/memory/vram flag. Only `--config <json>` — but the
   binary exposes no arena/virtual/vmm JSON key.
2. No memory env var in the binary (only `LFS_VK_*`, `LFS_PYTHON_LSP*`,
   `LFS_DEV_HOT_RELOAD`, `LFS_RML_DEBUGGER` — none memory-related).
3. Upstream issues #792 (our exact cascade) and #1091 (memory_arena OOM) are both
   open, unresolved, with no documented env/flag/config workaround.

**Action taken.** No launch-flag fix exists, so per the billed-resource rules both
idle, fundamentally-blocked pods were terminated (`podTerminate` → verified absent;
lane 2 `xyljs5kh9s2l6h` left running). Bleed stopped ~20:37Z. The two mid-run
checkpoints were on pod-local disk and were destroyed with the pods. Cells
`tile_2_1` and `tile_2_2` remain UNBUILT.

**Binding on future fleet launches (once a path is chosen):**
- Do NOT relaunch these two cells on any stock 48/80 GB pod with the current build
  and the locked recipe — the 32 GB arena wall is card-independent; it will crash
  the same way. Treat a stock-build relaunch as a known-doomed run.
- Route decision is Joel's (recipe is locked: 12M cap / native 8192 / mrnf). Options:
  - **(a) Patch + rebuild** `memory_arena.cu` to raise the hardcoded 32 GB virtual
    reservation toward physical (e.g. 44 GB on a 48 GB card) and rebuild LichtFeld.
    The real fix. Needs re-clone + recompile on a fresh pod; canary ONE cell before
    committing the fleet. (Whether native-8192/12M still overflows a raised arena is
    unverified — measure the new peak on the canary.)
  - **(b) 80 GB card, stock build:** only helps IF the sort buffer's raw allocation
    lives outside the 32 GB arena VA reservation. The H200 (141 GB) in #792 still
    crashed with `virtual=32`, so this is a MAYBE, not a guarantee — canary first.
  - **(c) Lower per-cell cap** (e.g. 8M) to shrink the sort buffer — **violates the
    locked 12M recipe; Joel's call only.**

### STAGED FOR SKYCHIEF (apply when the PC is reachable — deferred, Autologon in progress)

Append to `C:\LidargraphCapture\status\ADVANCE_PROCEDURE.txt`:
> ARENA WALL (2026-07-21): LichtFeld's CUDA arena is a HARDCODED 32 GB virtual
> reservation, card-independent (same on A6000/A40/H200). Native-8192 + 12M-cap
> cells whose FastGS forward sort buffer crosses 32 GB crash at forward.cu:60
> ("FastGS sort-buffer allocation" -> cudaErrorInvalidDevice cascade) with 28+ GB
> of the card idle. Bigger cards do NOT raise the wall. There is no flag/env/config
> to change it. A stock-build relaunch of such a cell is a known-doomed run — do not
> launch it. Fix requires a patched+rebuilt binary (raise the 32 GB constant) or
> Joel's approval to lower the cap. Canary one cell after any change.

Fleet ledger line (append on Skychief):
> 2026-07-21 20:37Z | tile_2_1 (pod v6e0szp7n6odbz, A6000) crash iter 11968, arena
> peak 19143 MB / virtual 32 GB | tile_2_2 (pod a6x3d2clt1ziqy, A40) crash iter 7965,
> peak 17197 MB / virtual 32 GB | cause: hardcoded 32 GB arena wall (card-independent),
> no config fix | both pods TERMINATED (verified absent), lane2 xyljs5kh9s2l6h left
> running | cells tile_2_1, tile_2_2 UNBUILT, awaiting Joel's route decision.
