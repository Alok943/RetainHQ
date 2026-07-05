# Critic Report: NCERT Physics (Class 9-10) KC Graph

## 1. Coverage Sweep (Orphan exercise types)
After walking through the NCERT chapter exercises, I found a few problem types and concepts that were completely orphaned (missing) from the graph:

1. **Relative Density (Class 9 Gravitation):** Numericals often ask to compare the density of a substance to water (e.g., "Relative density of silver is 10.8..."). This is missing.
2. **Multiple Reflections / Reverberation (Class 9 Sound):** The graph covers echoes (single reflection) but misses the applications of multiple reflections (stethoscopes, megaphones, concert hall acoustics).
3. **Relative Refractive Index (Class 10 Light):** The graph only covers absolute refractive index ($n = c/v$). It misses $n_{21} = v_1 / v_2$, which is heavily tested in numericals ("Light enters from glass to water...").
4. **Magnetic field of a circular loop (Class 10 Magnetic Effects):** The graph covers straight conductors and solenoids, but misses the circular loop (clock face rule), which is explicitly taught and tested.

## 2. Edge Audit (Sampled 15 edges)
I sampled 15 edges and checked the justification: *"a student who has NOT mastered A will predictably fail B"*.

**FAILED EDGE:**
- `Identify myopia (near-sightedness)` depends on `Calculate power of a lens`.
  *Criticism:* A student can absolutely identify that they can't see distant objects (myopia) and memorize that it needs a concave lens, without knowing how to calculate diopters ($P = 1/f$). The dependency is backwards or nonexistent. 
- `Identify hypermetropia (far-sightedness)` depends on `Calculate power of a lens`.
  *Criticism:* Same as above.
  
**CORRECTION:** Remove the edge from `Calculate power of a lens` to the defect identifications. Instead, make `Calculate power for vision correction` depend on BOTH identifying the defect AND calculating the power of a lens.

**PASSED EDGES:**
- `Read coordinates from a line graph` $\rightarrow$ `Sign convention for coordinates` (Valid: you need to know what axes are before you assign +/-).
- `Define work done by a constant force` $\rightarrow$ `Define electric potential difference` (Valid: $V = W/Q$ relies on the mechanical definition of Work).
- `Apply F = ma` $\rightarrow$ `Identify conditions for magnetic force` (Valid: understanding force scaling conceptually relies on basic force).
- `Identify cause of refraction` $\rightarrow$ `Predict bending of light` (Valid: understanding speed change is required to reason about bending towards/away from normal).

## 3. Grain Audit
I reviewed the 5 coarsest and 5 finest KCs against the prompt's calibration examples.

- **Too Coarse?** `"Draw ray diagrams for concave mirrors"` covers 6 distinct object positions. A student often masters the real-image cases (beyond C, at C, between C and F) while failing the virtual-image case (between F and P).
  *Criticism:* It should be split into `Draw ray diagrams for concave mirrors (real images)` and `Draw ray diagrams for concave mirrors (virtual image)`.
- **Too Fine?** `"Identify conventional current direction"` is very close to a micro-skill, but because it actively contradicts the flow of electrons (a major point of confusion for beginners), it justifies its existence as a standalone KC to test.

## 4. Cycle & Dangling-Title Check
*(Automatically verified via the Python script prior to submission. No cycles, no dangling titles.)*

---

## Action Plan (FIX_LIST)
1. **[ADD]** KC: `Define relative density` (Gravitation).
2. **[ADD]** KC: `Describe applications of multiple reflections of sound` (Sound).
3. **[ADD]** KC: `Apply relative refractive index` (Light).
4. **[ADD]** KC: `Describe magnetic field of a circular loop` (Magnetic Effects).
5. **[MODIFY]** Edges for Eye defects: Remove `Calculate power of a lens` as a prerequisite for `Identify myopia` and `Identify hypermetropia`.
6. **[SPLIT]** `Draw ray diagrams for concave mirrors` into `(real images)` and `(virtual image)`.
