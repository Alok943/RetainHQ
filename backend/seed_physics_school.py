"""
Seed script: NCERT Physics (Class 9-10) as a RetainHQ roadmap — the SCHOOL platform spine.

Knowledge-component graph authored by Antigravity against content/PROMPT-physics-kc-graph.md
(artifacts + critic report: content/research/physics/). Post-audit fixes applied:
definitional edges added (velocity<-displacement, acceleration<-velocity, Ohm's law<-V,I),
transitive-redundant edges removed. 126 KCs; edges live in
seed_physics_school_prereqs.py (140 edges, 8 cross-year Class 9->10).

audience='school' — the roadmaps.audience gate (migration c4d7e9a2b501 + user_prefs)
keeps this out of the 'career' catalog, so college users never see it and school
users see only it. Run migrations to head before seeding in prod.

Idempotent — deletes and recreates this roadmap each run (wipes its user_progress).
Run: ./.venv/Scripts/python.exe seed_physics_school.py  (then seed_physics_school_prereqs.py)
"""
import asyncio
import uuid
from sqlalchemy import text
from app.core.database import engine

ROADMAP_ID = uuid.UUID("f1f1f1f1-f1f1-f1f1-f1f1-f1f1f1f1f1f1")
TITLE = "Physics — Class 9 & 10 (NCERT)"
SLUG = "physics-9-10"
DESCRIPTION = "Every physics concept from the Class 9 and 10 NCERT textbooks as one prerequisite graph — so you can see exactly which earlier idea is blocking you, and never walk into boards having forgotten August's chapters."

# (phase, section, title, tier, recall_hint)
NODES = [
    # ---------------- Class 9 · Motion ----------------
    ("Class 9 · Motion", "Math tools", "Convert km/h to m/s", "easy", "Multiply by 5/18 to convert km/h to m/s."),
    ("Class 9 · Motion", "Math tools", "Read coordinates from a line graph", "easy", "Identify x (horizontal) and y (vertical) values for a given point."),
    ("Class 9 · Motion", "Math tools", "Calculate the slope of a straight line", "medium", "Slope = change in y / change in x (rise over run)."),
    ("Class 9 · Motion", "Math tools", "Calculate area of triangle and rectangle", "easy", "Area = 1/2 * base * height (triangle); Area = length * width (rectangle)."),
    ("Class 9 · Motion", "Math tools", "Rearrange linear algebraic equations", "medium", "Isolate the unknown variable using inverse operations."),
    ("Class 9 · Motion", "Describing motion", "Define distance", "easy", "Distance is the actual path length covered by an object."),
    ("Class 9 · Motion", "Describing motion", "Define displacement", "easy", "Displacement is the shortest straight-line distance from initial to final position."),
    ("Class 9 · Motion", "Describing motion", "Distinguish distance from displacement", "easy", "Distance = path length (scalar); displacement = shortest start->end vector; can be zero."),
    ("Class 9 · Motion", "Describing motion", "Determine if displacement is zero", "medium", "Displacement is zero if the object returns to its starting point."),
    ("Class 9 · Motion", "Rate of motion", "Define average speed", "easy", "Average speed = total distance / total time."),
    ("Class 9 · Motion", "Rate of motion", "Apply average speed formula", "medium", "Use v = s/t to find total distance, total time, or average speed."),
    ("Class 9 · Motion", "Rate of motion", "Define velocity", "easy", "Velocity is speed with a specific direction (displacement / time)."),
    ("Class 9 · Motion", "Rate of motion", "Distinguish speed from velocity", "easy", "Speed is scalar (magnitude only), velocity is vector (magnitude + direction)."),
    ("Class 9 · Motion", "Rate of motion", "Calculate average velocity", "medium", "Average velocity = total displacement / total time, or (u+v)/2 for uniform acceleration."),
    ("Class 9 · Motion", "Rate of change of velocity", "Define acceleration", "easy", "Acceleration is the rate of change of velocity: a = (v-u)/t."),
    ("Class 9 · Motion", "Rate of change of velocity", "Distinguish uniform and non-uniform acceleration", "easy", "Uniform = velocity changes by equal amounts in equal times."),
    ("Class 9 · Motion", "Rate of change of velocity", "Interpret sign of acceleration", "medium", "Positive acceleration increases speed; negative acceleration (retardation) decreases speed."),
    ("Class 9 · Motion", "Rate of change of velocity", "Apply acceleration formula", "medium", "Calculate a, v, u, or t using a = (v-u)/t."),
    ("Class 9 · Motion", "Graphical representation", "Interpret stationary object on distance-time graph", "easy", "A horizontal line parallel to the time axis means the object is at rest."),
    ("Class 9 · Motion", "Graphical representation", "Interpret uniform motion on distance-time graph", "easy", "A straight sloped line indicates uniform speed."),
    ("Class 9 · Motion", "Graphical representation", "Read speed off a distance-time graph", "medium", "Speed is the slope of the distance-time graph."),
    ("Class 9 · Motion", "Graphical representation", "Interpret uniform velocity on velocity-time graph", "easy", "A horizontal line means velocity is constant (zero acceleration)."),
    ("Class 9 · Motion", "Graphical representation", "Interpret uniform acceleration on velocity-time graph", "easy", "A straight sloped line indicates uniform acceleration."),
    ("Class 9 · Motion", "Graphical representation", "Read acceleration off a velocity-time graph", "medium", "Acceleration is the slope of the velocity-time graph."),
    ("Class 9 · Motion", "Graphical representation", "Read displacement off a velocity-time graph", "hard", "Displacement is the area under the velocity-time curve."),
    ("Class 9 · Motion", "Equations of motion", "Select correct equation of motion", "medium", "Choose equation based on the knowns and the single unknown you need to find."),
    ("Class 9 · Motion", "Equations of motion", "Apply v = u + at", "medium", "First equation of motion; relates velocity, acceleration, and time (no displacement)."),
    ("Class 9 · Motion", "Equations of motion", "Apply s = ut + 1/2 at^2", "hard", "Second equation of motion; relates displacement, time, and acceleration (no final velocity)."),
    ("Class 9 · Motion", "Equations of motion", "Apply 2as = v^2 - u^2", "hard", "Third equation of motion; relates velocity, acceleration, and displacement (no time)."),
    ("Class 9 · Motion", "Uniform circular motion", "Identify uniform circular motion as accelerated", "medium", "Direction changes continuously, so velocity changes, meaning it's accelerated."),
    ("Class 9 · Motion", "Uniform circular motion", "Calculate speed in circular motion", "medium", "Speed v = 2*pi*r / T, where T is the time for one revolution."),

    # ---------------- Class 9 · Force and Laws of Motion ----------------
    ("Class 9 · Force and Laws of Motion", "Balanced and unbalanced forces", "Distinguish balanced and unbalanced forces", "easy", "Balanced forces don't change state of motion; unbalanced forces cause acceleration."),
    ("Class 9 · Force and Laws of Motion", "First law of motion", "State Newton's first law of motion", "easy", "Object remains at rest or in uniform motion unless acted upon by unbalanced force."),
    ("Class 9 · Force and Laws of Motion", "First law of motion", "Define inertia", "easy", "Inertia is the natural tendency of an object to resist a change in its state of motion."),
    ("Class 9 · Force and Laws of Motion", "First law of motion", "Relate inertia to mass", "easy", "Mass is the quantitative measure of an object's inertia; heavier = more inertia."),
    ("Class 9 · Force and Laws of Motion", "Second law of motion", "Define momentum", "easy", "Momentum p = mass * velocity. It is a vector quantity."),
    ("Class 9 · Force and Laws of Motion", "Second law of motion", "State Newton's second law of motion", "easy", "Rate of change of momentum is proportional to the applied unbalanced force."),
    ("Class 9 · Force and Laws of Motion", "Second law of motion", "Apply F = ma", "medium", "Net force equals mass times acceleration."),
    ("Class 9 · Force and Laws of Motion", "Third law of motion", "State Newton's third law of motion", "easy", "To every action, there is an equal and opposite reaction acting on different bodies."),
    ("Class 9 · Force and Laws of Motion", "Third law of motion", "Identify action-reaction pairs", "medium", "Forces occur in pairs acting on two different interacting objects."),

    # ---------------- Class 9 · Gravitation ----------------
    ("Class 9 · Gravitation", "Universal law of gravitation", "State the universal law of gravitation", "easy", "Every object attracts every other object with a force proportional to product of masses and inversely proportional to square of distance."),
    ("Class 9 · Gravitation", "Universal law of gravitation", "Apply F = G m1 m2 / r^2", "hard", "Calculate gravitational force between two bodies."),
    ("Class 9 · Gravitation", "Free fall", "Define free fall", "easy", "Motion of an object under the influence of gravitational force alone."),
    ("Class 9 · Gravitation", "Free fall", "State acceleration due to gravity (g)", "easy", "g = 9.8 m/s^2 near earth's surface, independent of the object's mass."),
    ("Class 9 · Gravitation", "Free fall", "Apply equations of motion for free fall", "hard", "Use v=u+gt, h=ut+1/2gt^2, 2gh=v^2-u^2 with correct sign convention for g."),
    ("Class 9 · Gravitation", "Mass and weight", "Distinguish mass and weight", "easy", "Mass is amount of matter (scalar, constant); weight is force of gravity W = mg (vector, varies)."),
    ("Class 9 · Gravitation", "Mass and weight", "Calculate weight on earth and moon", "medium", "Weight on moon is 1/6th of weight on earth because moon's gravity is 1/6th."),
    ("Class 9 · Gravitation", "Thrust and pressure", "Define thrust", "easy", "Thrust is the net force acting perpendicular to a surface."),
    ("Class 9 · Gravitation", "Thrust and pressure", "Define pressure", "easy", "Pressure = thrust / area. Unit is Pascal (Pa)."),
    ("Class 9 · Gravitation", "Thrust and pressure", "Apply Pressure = Force / Area", "medium", "Calculate pressure given force and area, recognizing that smaller area = higher pressure."),
    ("Class 9 · Gravitation", "Buoyancy", "Define buoyant force", "easy", "The upward force exerted by a fluid on an object immersed in it."),
    ("Class 9 · Gravitation", "Buoyancy", "Determine if an object floats or sinks", "medium", "Floats if density < fluid density; sinks if density > fluid density."),
    ("Class 9 · Gravitation", "Archimedes principle", "State Archimedes principle", "easy", "Buoyant force equals the weight of the fluid displaced by the object."),
    ("Class 9 · Gravitation", "Relative Density", "Define relative density", "easy", "Ratio of density of a substance to the density of water. No units."),

    # ---------------- Class 9 · Work and Energy ----------------
    ("Class 9 · Work and Energy", "Work", "Define work done by a constant force", "easy", "Work = force * displacement in the direction of the force (W = F s)."),
    ("Class 9 · Work and Energy", "Work", "Identify zero work conditions", "medium", "Work is zero if displacement is zero or if force is perpendicular to displacement."),
    ("Class 9 · Work and Energy", "Work", "Interpret negative work", "medium", "Work is negative if force acts opposite to the direction of displacement (e.g. friction)."),
    ("Class 9 · Work and Energy", "Energy", "Define energy", "easy", "Energy is the capacity to do work. Unit is Joule (J)."),
    ("Class 9 · Work and Energy", "Kinetic energy", "Apply kinetic energy formula", "medium", "Kinetic energy Ek = 1/2 m v^2."),
    ("Class 9 · Work and Energy", "Kinetic energy", "Relate work to change in kinetic energy", "hard", "Work-energy theorem: Work done on object = change in kinetic energy."),
    ("Class 9 · Work and Energy", "Potential energy", "Define gravitational potential energy", "easy", "Energy possessed by virtue of position or height above ground."),
    ("Class 9 · Work and Energy", "Potential energy", "Apply potential energy formula", "medium", "Potential energy Ep = mgh."),
    ("Class 9 · Work and Energy", "Conservation of energy", "State law of conservation of energy", "easy", "Energy can neither be created nor destroyed, only transformed."),
    ("Class 9 · Work and Energy", "Conservation of energy", "Calculate mechanical energy of free falling object", "hard", "Sum of KE and PE remains constant during free fall."),
    ("Class 9 · Work and Energy", "Power", "Define power", "easy", "Power is the rate of doing work or rate of transfer of energy: P = W/t."),
    ("Class 9 · Work and Energy", "Power", "Apply power formula", "medium", "Calculate power in Watts (W) given work and time, or P = E/t."),
    ("Class 9 · Work and Energy", "Power", "Convert commercial unit of energy", "medium", "1 kWh = 1 unit = 3.6 x 10^6 J."),

    # ---------------- Class 9 · Sound ----------------
    ("Class 9 · Sound", "Production and propagation", "Identify sound as a mechanical wave", "easy", "Sound requires a material medium to propagate; cannot travel in vacuum."),
    ("Class 9 · Sound", "Production and propagation", "Distinguish longitudinal and transverse waves", "medium", "Sound is longitudinal (particles oscillate parallel to wave direction, forming compressions/rarefactions)."),
    ("Class 9 · Sound", "Characteristics of sound", "Define frequency, time period, and wavelength", "easy", "Wavelength (lambda) is distance between compressions; Frequency (nu) is oscillations per second; T = 1/nu."),
    ("Class 9 · Sound", "Characteristics of sound", "Apply wave speed equation", "medium", "Speed = wavelength * frequency (v = lambda * nu)."),
    ("Class 9 · Sound", "Characteristics of sound", "Relate pitch to frequency", "easy", "Higher frequency means higher pitch."),
    ("Class 9 · Sound", "Characteristics of sound", "Relate loudness to amplitude", "easy", "Loudness depends on the amplitude of the sound wave."),
    ("Class 9 · Sound", "Reflection of sound", "State laws of reflection of sound", "easy", "Angle of incidence = angle of reflection, in the same plane."),
    ("Class 9 · Sound", "Reflection of sound", "Calculate distance using echo", "medium", "Total distance = 2d. Speed = 2d/t."),
    ("Class 9 · Sound", "Reflection of sound", "Describe applications of multiple reflections of sound", "easy", "Megaphones, stethoscopes, and concert halls use repeated reflection to direct sound."),
    ("Class 9 · Sound", "Range of hearing", "State the audible range for humans", "easy", "20 Hz to 20,000 Hz. Below = infrasound, above = ultrasound."),

    # ---------------- Class 10 · Light ----------------
    ("Class 10 · Light", "Math tools", "Cross-multiplication in proportions", "medium", "Solve a/b = c/d by cross multiplying ad = bc."),
    ("Class 10 · Light", "Math tools", "Sign convention for coordinates", "medium", "Use Cartesian sign convention: left/down is negative, right/up is positive."),

    # ---------------- Class 10 · Electricity ----------------
    ("Class 10 · Electricity", "Math tools", "Calculate inverse sums", "hard", "Solve 1/R = 1/R1 + 1/R2 by finding common denominators."),

    # ---------------- Class 10 · Light ----------------
    ("Class 10 · Light", "Reflection by spherical mirrors", "Identify concave and convex mirrors", "easy", "Concave curves inward (converging); convex curves outward (diverging)."),
    ("Class 10 · Light", "Reflection by spherical mirrors", "Define principal focus and focal length", "medium", "Point where parallel rays converge (concave) or appear to diverge from (convex). f = R/2."),
    ("Class 10 · Light", "Reflection by spherical mirrors", "Draw ray diagrams for concave mirrors (real images)", "hard", "Use standard rays to find real/inverted images for objects placed beyond the focal point."),
    ("Class 10 · Light", "Reflection by spherical mirrors", "Draw ray diagrams for concave mirrors (virtual image)", "medium", "Use standard rays to find the virtual/erect image for an object placed between the pole and focus."),
    ("Class 10 · Light", "Reflection by spherical mirrors", "Draw ray diagrams for convex mirrors", "medium", "Image is always virtual, erect, and diminished."),
    ("Class 10 · Light", "Mirror formula", "Apply mirror sign convention", "medium", "Object distance (u) is always negative; focal length of concave is -, convex is +."),
    ("Class 10 · Light", "Mirror formula", "Apply mirror formula", "hard", "Use 1/v + 1/u = 1/f to find image position."),
    ("Class 10 · Light", "Mirror formula", "Calculate linear magnification (mirrors)", "medium", "m = h'/h = -v/u. Negative m means real image."),
    ("Class 10 · Light", "Refraction", "Identify cause of refraction", "easy", "Change in speed of light when entering a different medium."),
    ("Class 10 · Light", "Refraction", "Apply laws of refraction (Snell's Law)", "hard", "Ratio of sin(i) to sin(r) is constant (refractive index)."),
    ("Class 10 · Light", "Refraction", "Relate refractive index to speed of light", "medium", "Absolute refractive index n = c/v."),
    ("Class 10 · Light", "Refraction", "Apply relative refractive index", "hard", "Relative refractive index n21 = v1 / v2. It compares the speed in medium 1 to medium 2."),
    ("Class 10 · Light", "Refraction", "Predict bending of light", "medium", "Rarer to denser bends toward normal; denser to rarer bends away from normal."),
    ("Class 10 · Light", "Spherical lenses", "Identify convex and concave lenses", "easy", "Convex is thick in middle (converging); concave is thin in middle (diverging)."),
    ("Class 10 · Light", "Spherical lenses", "Draw ray diagrams for convex lenses", "hard", "Use standard rays to find real or virtual images depending on object position."),
    ("Class 10 · Light", "Lens formula", "Apply lens sign convention", "medium", "Convex f is positive, concave f is negative; u is always negative."),
    ("Class 10 · Light", "Lens formula", "Apply lens formula", "hard", "Use 1/v - 1/u = 1/f to find image position."),
    ("Class 10 · Light", "Lens formula", "Calculate linear magnification (lenses)", "medium", "m = h'/h = v/u. Negative m means real/inverted."),
    ("Class 10 · Light", "Lens formula", "Calculate power of a lens", "medium", "Power P = 1/f (in meters). Unit is Diopter (D)."),

    # ---------------- Class 10 · Eye ----------------
    ("Class 10 · Eye", "Defects of vision", "Identify myopia (near-sightedness)", "easy", "Can see near objects clearly, distant objects blurry. Corrected with concave lens."),
    ("Class 10 · Eye", "Defects of vision", "Identify hypermetropia (far-sightedness)", "easy", "Can see distant objects clearly, near objects blurry. Corrected with convex lens."),
    ("Class 10 · Eye", "Defects of vision", "Calculate power for vision correction", "hard", "Use lens formula where v is the far/near point, to find required f and P."),
    ("Class 10 · Eye", "Refraction through prism", "Describe dispersion of white light", "easy", "Splitting of white light into 7 colors (VIBGYOR) by a prism due to different bending angles."),
    ("Class 10 · Eye", "Atmospheric refraction", "Explain twinkling of stars", "medium", "Varying atmospheric density causes continuous refraction and shifting of apparent star position."),
    ("Class 10 · Eye", "Scattering of light", "Explain blue color of sky", "medium", "Fine particles in atmosphere scatter shorter wavelengths (blue) more strongly than longer (red)."),

    # ---------------- Class 10 · Electricity ----------------
    ("Class 10 · Electricity", "Electric current", "Define electric current", "easy", "Current I = Q/t, rate of flow of electric charge. Unit is Ampere (A)."),
    ("Class 10 · Electricity", "Electric current", "Identify conventional current direction", "easy", "Flows from positive to negative terminal, opposite to electron flow."),
    ("Class 10 · Electricity", "Potential difference", "Define electric potential difference", "medium", "Work done per unit charge (V = W/Q) to move it between two points. Unit is Volt (V)."),
    ("Class 10 · Electricity", "Circuit diagram", "Identify symbols in a circuit diagram", "easy", "Recognize cell, battery, resistor, ammeter (series), voltmeter (parallel), switch."),
    ("Class 10 · Electricity", "Ohm's law", "State Ohm's Law", "medium", "V is directly proportional to I, provided temperature is constant (V = IR)."),
    ("Class 10 · Electricity", "Ohm's law", "Apply Ohm's law to circuits", "medium", "Calculate V, I, or R using V = IR."),
    ("Class 10 · Electricity", "Resistance", "Identify factors affecting resistance", "medium", "R depends directly on length, inversely on cross-sectional area, and material nature."),
    ("Class 10 · Electricity", "Resistance", "Apply resistivity formula", "hard", "R = rho * L / A. Calculate resistivity or dimensions."),
    ("Class 10 · Electricity", "System of resistors", "Calculate equivalent resistance in series", "medium", "Rs = R1 + R2 + R3. Current is same, voltage divides."),
    ("Class 10 · Electricity", "System of resistors", "Calculate equivalent resistance in parallel", "hard", "1/Rp = 1/R1 + 1/R2. Voltage is same, current divides."),
    ("Class 10 · Electricity", "System of resistors", "Solve complex resistor networks", "hard", "Break down mixed series/parallel circuits into equivalent resistances step-by-step."),
    ("Class 10 · Electricity", "Heating effect", "Calculate heat generated by current", "medium", "Joule's law of heating: H = I^2 R t."),
    ("Class 10 · Electricity", "Electric power", "Apply electric power formulas", "medium", "P = VI = I^2 R = V^2 / R."),

    # ---------------- Class 10 · Magnetic Effects ----------------
    ("Class 10 · Magnetic Effects", "Magnetic field", "Describe magnetic field lines", "easy", "Emerge from North, merge at South; closer lines = stronger field; never intersect."),
    ("Class 10 · Magnetic Effects", "Magnetic field due to current", "Apply Right-Hand Thumb Rule", "medium", "Thumb points to current, curling fingers show direction of circular magnetic field lines."),
    ("Class 10 · Magnetic Effects", "Magnetic field due to current", "Describe magnetic field of a circular loop", "medium", "Concentric circles at every point; straight lines at the center. Polarity by clock face rule."),
    ("Class 10 · Magnetic Effects", "Magnetic field due to current", "Describe field of a solenoid", "medium", "Inside is uniform and parallel (like a bar magnet). Used to make electromagnets."),
    ("Class 10 · Magnetic Effects", "Force on current conductor", "Identify conditions for magnetic force", "medium", "A current carrying conductor in a magnetic field experiences a force, maximum when perpendicular."),
    ("Class 10 · Magnetic Effects", "Force on current conductor", "Apply Fleming's Left-Hand Rule", "hard", "Thumb=Force, Forefinger=Field, Middle=Current. All three mutually perpendicular."),
    ("Class 10 · Magnetic Effects", "Electromagnetic induction", "Describe electromagnetic induction", "medium", "Moving a magnet in/out of a coil (or vice versa) induces a current — Faraday's discovery."),
    ("Class 10 · Magnetic Effects", "Electromagnetic induction", "Apply Fleming's Right-Hand Rule", "hard", "Thumb=Motion, Forefinger=Field, Middle=induced Current. Used for generators, not motors."),
    ("Class 10 · Magnetic Effects", "Domestic circuits", "Distinguish live, neutral, and earth wires", "easy", "Live (red/brown, 220V), Neutral (black/blue, 0V), Earth (green/yellow, safety)."),
    ("Class 10 · Magnetic Effects", "Domestic circuits", "Explain role of a fuse", "easy", "Melts to break circuit if current exceeds safe limit, preventing fire/damage."),
]


async def main():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM roadmap_nodes WHERE roadmap_id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(text("DELETE FROM roadmaps WHERE id = :rid"), {"rid": str(ROADMAP_ID)})
        await conn.execute(
            text("INSERT INTO roadmaps (id, slug, title, description, audience, created_at) "
                 "VALUES (:id, :slug, :title, :desc, 'school', now())"),
            {"id": str(ROADMAP_ID), "slug": SLUG, "title": TITLE, "desc": DESCRIPTION},
        )
        for i, (phase, section, title, tier, desc) in enumerate(NODES):
            await conn.execute(
                text("INSERT INTO roadmap_nodes "
                     "(id, roadmap_id, phase, section, title, tier, order_index, description) "
                     "VALUES (:id, :rid, :phase, :section, :title, :tier, :idx, :desc)"),
                {"id": str(uuid.uuid4()), "rid": str(ROADMAP_ID), "phase": phase,
                 "section": section, "title": title, "tier": tier, "idx": i, "desc": desc},
            )
    print(f"Seeded '{TITLE}' with {len(NODES)} nodes.")


if __name__ == "__main__":
    asyncio.run(main())
