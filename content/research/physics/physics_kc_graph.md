# NCERT Physics (Class 9-10) Knowledge-Component Graph

Here is the complete concept inventory and prerequisite graph for NCERT Science - Physics (Class 9 and Class 10 CBSE), mapped out for the retention engine.

```python
# (phase, section, title, tier, recall_hint)
NODES = [
    # MATH TOOLS
    ("Class 9 · Motion", "Math tools", "Convert km/h to m/s", "easy", "Multiply by 5/18 to convert km/h to m/s."),
    ("Class 9 · Motion", "Math tools", "Read coordinates from a line graph", "easy", "Identify x (horizontal) and y (vertical) values for a given point."),
    ("Class 9 · Motion", "Math tools", "Calculate the slope of a straight line", "medium", "Slope = change in y / change in x (rise over run)."),
    ("Class 9 · Motion", "Math tools", "Calculate area of triangle and rectangle", "easy", "Area = 1/2 * base * height (triangle); Area = length * width (rectangle)."),
    ("Class 9 · Motion", "Math tools", "Rearrange linear algebraic equations", "medium", "Isolate the unknown variable using inverse operations."),

    # MOTION
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

    # FORCE AND LAWS OF MOTION
    ("Class 9 · Force and Laws of Motion", "Balanced and unbalanced forces", "Distinguish balanced and unbalanced forces", "easy", "Balanced forces don't change state of motion; unbalanced forces cause acceleration."),
    ("Class 9 · Force and Laws of Motion", "First law of motion", "State Newton's first law of motion", "easy", "Object remains at rest or in uniform motion unless acted upon by unbalanced force."),
    ("Class 9 · Force and Laws of Motion", "First law of motion", "Define inertia", "easy", "Inertia is the natural tendency of an object to resist a change in its state of motion."),
    ("Class 9 · Force and Laws of Motion", "First law of motion", "Relate inertia to mass", "easy", "Mass is the quantitative measure of an object's inertia; heavier = more inertia."),
    ("Class 9 · Force and Laws of Motion", "Second law of motion", "Define momentum", "easy", "Momentum p = mass * velocity. It is a vector quantity."),
    ("Class 9 · Force and Laws of Motion", "Second law of motion", "State Newton's second law of motion", "easy", "Rate of change of momentum is proportional to the applied unbalanced force."),
    ("Class 9 · Force and Laws of Motion", "Second law of motion", "Apply F = ma", "medium", "Net force equals mass times acceleration."),
    ("Class 9 · Force and Laws of Motion", "Third law of motion", "State Newton's third law of motion", "easy", "To every action, there is an equal and opposite reaction acting on different bodies."),
    ("Class 9 · Force and Laws of Motion", "Third law of motion", "Identify action-reaction pairs", "medium", "Forces occur in pairs acting on two different interacting objects."),

    # GRAVITATION
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

    # WORK AND ENERGY
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

    # SOUND
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

    # CLASS 10 MATH TOOLS
    ("Class 10 · Light", "Math tools", "Cross-multiplication in proportions", "medium", "Solve a/b = c/d by cross multiplying ad = bc."),
    ("Class 10 · Light", "Math tools", "Sign convention for coordinates", "medium", "Use Cartesian sign convention: left/down is negative, right/up is positive."),
    ("Class 10 · Electricity", "Math tools", "Calculate inverse sums", "hard", "Solve 1/R = 1/R1 + 1/R2 by finding common denominators."),

    # LIGHT - REFLECTION AND REFRACTION
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

    # THE HUMAN EYE AND THE COLOURFUL WORLD
    ("Class 10 · Eye", "Defects of vision", "Identify myopia (near-sightedness)", "easy", "Can see near objects clearly, distant objects blurry. Corrected with concave lens."),
    ("Class 10 · Eye", "Defects of vision", "Identify hypermetropia (far-sightedness)", "easy", "Can see distant objects clearly, near objects blurry. Corrected with convex lens."),
    ("Class 10 · Eye", "Defects of vision", "Calculate power for vision correction", "hard", "Use lens formula where v is the far/near point, to find required f and P."),
    ("Class 10 · Eye", "Refraction through prism", "Describe dispersion of white light", "easy", "Splitting of white light into 7 colors (VIBGYOR) by a prism due to different bending angles."),
    ("Class 10 · Eye", "Atmospheric refraction", "Explain twinkling of stars", "medium", "Varying atmospheric density causes continuous refraction and shifting of apparent star position."),
    ("Class 10 · Eye", "Scattering of light", "Explain blue color of sky", "medium", "Fine particles in atmosphere scatter shorter wavelengths (blue) more strongly than longer (red)."),

    # ELECTRICITY
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

    # MAGNETIC EFFECTS OF ELECTRIC CURRENT
    ("Class 10 · Magnetic Effects", "Magnetic field", "Describe magnetic field lines", "easy", "Emerge from North, merge at South; closer lines = stronger field; never intersect."),
    ("Class 10 · Magnetic Effects", "Magnetic field due to current", "Apply Right-Hand Thumb Rule", "medium", "Thumb points to current, curling fingers show direction of circular magnetic field lines."),
    ("Class 10 · Magnetic Effects", "Magnetic field due to current", "Describe magnetic field of a circular loop", "medium", "Concentric circles at every point; straight lines at the center. Polarity by clock face rule."),
    ("Class 10 · Magnetic Effects", "Magnetic field due to current", "Describe field of a solenoid", "medium", "Inside is uniform and parallel (like a bar magnet). Used to make electromagnets."),
    ("Class 10 · Magnetic Effects", "Force on current conductor", "Identify conditions for magnetic force", "medium", "A current carrying conductor in a magnetic field experiences a force, maximum when perpendicular."),
    ("Class 10 · Magnetic Effects", "Force on current conductor", "Apply Fleming's Left-Hand Rule", "hard", "Thumb=Force, Forefinger=Field, Middle=Current. All three mutually perpendicular."),
    ("Class 10 · Magnetic Effects", "Domestic circuits", "Distinguish live, neutral, and earth wires", "easy", "Live (red/brown, 220V), Neutral (black/blue, 0V), Earth (green/yellow, safety)."),
    ("Class 10 · Magnetic Effects", "Domestic circuits", "Explain role of a fuse", "easy", "Melts to break circuit if current exceeds safe limit, preventing fire/damage.")
]

# title -> [titles that must be mastered BEFORE it]
PREREQS = {
    # MATH TOOLS
    "Calculate the slope of a straight line": ["Read coordinates from a line graph"],
    
    # MOTION
    "Define displacement": ["Define distance"],
    "Distinguish distance from displacement": ["Define distance", "Define displacement"],
    "Determine if displacement is zero": ["Define displacement"],
    
    "Apply average speed formula": ["Define average speed", "Rearrange linear algebraic equations"],
    "Distinguish speed from velocity": ["Define velocity", "Define average speed", "Distinguish distance from displacement"],
    "Calculate average velocity": ["Define velocity"],

    "Distinguish uniform and non-uniform acceleration": ["Define acceleration"],
    "Apply acceleration formula": ["Define acceleration", "Rearrange linear algebraic equations"],
    "Interpret sign of acceleration": ["Define acceleration"],

    "Interpret uniform motion on distance-time graph": ["Interpret stationary object on distance-time graph"],
    "Read speed off a distance-time graph": ["Calculate the slope of a straight line", "Interpret uniform motion on distance-time graph"],
    "Interpret uniform acceleration on velocity-time graph": ["Interpret uniform velocity on velocity-time graph"],
    "Read acceleration off a velocity-time graph": ["Calculate the slope of a straight line", "Interpret uniform acceleration on velocity-time graph"],
    "Read displacement off a velocity-time graph": ["Calculate area of triangle and rectangle", "Define displacement"],

    "Apply v = u + at": ["Define acceleration", "Rearrange linear algebraic equations"],
    "Apply s = ut + 1/2 at^2": ["Define acceleration", "Rearrange linear algebraic equations"],
    "Apply 2as = v^2 - u^2": ["Define acceleration", "Rearrange linear algebraic equations"],
    "Select correct equation of motion": ["Apply v = u + at", "Apply s = ut + 1/2 at^2", "Apply 2as = v^2 - u^2"],

    "Identify uniform circular motion as accelerated": ["Define velocity", "Define acceleration"],
    "Calculate speed in circular motion": ["Apply average speed formula"],

    # FORCE AND LAWS OF MOTION
    "State Newton's first law of motion": ["Distinguish balanced and unbalanced forces"],
    "Define inertia": ["State Newton's first law of motion"],
    "Relate inertia to mass": ["Define inertia"],
    
    "Define momentum": ["Define velocity"],
    "State Newton's second law of motion": ["Define momentum", "Define acceleration"],
    "Apply F = ma": ["State Newton's second law of motion", "Rearrange linear algebraic equations"],
    
    "Identify action-reaction pairs": ["State Newton's third law of motion", "Distinguish balanced and unbalanced forces"],

    # GRAVITATION
    "Apply F = G m1 m2 / r^2": ["State the universal law of gravitation", "Rearrange linear algebraic equations"],
    
    "State acceleration due to gravity (g)": ["Define free fall", "Define acceleration"],
    "Apply equations of motion for free fall": ["Apply v = u + at", "Apply s = ut + 1/2 at^2", "Apply 2as = v^2 - u^2", "State acceleration due to gravity (g)"],
    
    "Distinguish mass and weight": ["Relate inertia to mass", "Apply F = ma"],
    "Calculate weight on earth and moon": ["Distinguish mass and weight"],
    
    "Define pressure": ["Define thrust"],
    "Apply Pressure = Force / Area": ["Define pressure", "Rearrange linear algebraic equations"],
    
    "Determine if an object floats or sinks": ["Define buoyant force"],
    "State Archimedes principle": ["Define buoyant force"],

    # WORK AND ENERGY
    "Identify zero work conditions": ["Define work done by a constant force", "Determine if displacement is zero"],
    "Interpret negative work": ["Define work done by a constant force"],
    
    "Apply kinetic energy formula": ["Define energy", "Rearrange linear algebraic equations"],
    "Relate work to change in kinetic energy": ["Apply kinetic energy formula", "Define work done by a constant force", "Apply 2as = v^2 - u^2"],
    
    "Apply potential energy formula": ["Define gravitational potential energy", "Rearrange linear algebraic equations"],
    
    "Calculate mechanical energy of free falling object": ["State law of conservation of energy", "Apply potential energy formula", "Apply kinetic energy formula"],
    
    "Apply power formula": ["Define power", "Rearrange linear algebraic equations"],
    "Convert commercial unit of energy": ["Apply power formula"],

    # SOUND
    "Distinguish longitudinal and transverse waves": ["Identify sound as a mechanical wave"],
    
    "Apply wave speed equation": ["Define frequency, time period, and wavelength", "Rearrange linear algebraic equations"],
    "Relate pitch to frequency": ["Define frequency, time period, and wavelength"],
    "Relate loudness to amplitude": ["Define frequency, time period, and wavelength"],
    
    "Calculate distance using echo": ["State laws of reflection of sound", "Apply average speed formula"],
    "Describe applications of multiple reflections of sound": ["State laws of reflection of sound"],

    # CLASS 10 LIGHT
    "Cross-multiplication in proportions": ["Rearrange linear algebraic equations"],
    "Sign convention for coordinates": ["Read coordinates from a line graph"],
    
    "Define principal focus and focal length": ["Identify concave and convex mirrors"],
    "Draw ray diagrams for concave mirrors (real images)": ["Define principal focus and focal length"],
    "Draw ray diagrams for concave mirrors (virtual image)": ["Define principal focus and focal length"],
    "Draw ray diagrams for convex mirrors": ["Define principal focus and focal length"],
    
    "Apply mirror sign convention": ["Sign convention for coordinates", "Define principal focus and focal length"],
    "Apply mirror formula": ["Apply mirror sign convention", "Cross-multiplication in proportions"],
    "Calculate linear magnification (mirrors)": ["Apply mirror formula"],
    
    "Apply laws of refraction (Snell's Law)": ["Identify cause of refraction"],
    "Relate refractive index to speed of light": ["Identify cause of refraction", "Apply average speed formula"],
    "Apply relative refractive index": ["Relate refractive index to speed of light"],
    "Predict bending of light": ["Identify cause of refraction"],
    
    "Draw ray diagrams for convex lenses": ["Identify convex and concave lenses"],
    "Apply lens sign convention": ["Sign convention for coordinates", "Identify convex and concave lenses"],
    "Apply lens formula": ["Apply lens sign convention", "Cross-multiplication in proportions"],
    "Calculate linear magnification (lenses)": ["Apply lens formula"],
    "Calculate power of a lens": ["Apply lens formula"],

    # CLASS 10 EYE
    "Calculate power for vision correction": ["Identify myopia (near-sightedness)", "Identify hypermetropia (far-sightedness)", "Calculate power of a lens"],
    
    "Describe dispersion of white light": ["Predict bending of light"],
    "Explain twinkling of stars": ["Predict bending of light"],
    
    # CLASS 10 ELECTRICITY
    "Identify conventional current direction": ["Define electric current"],
    "Define electric potential difference": ["Define work done by a constant force"],
    
    "Apply Ohm's law to circuits": ["State Ohm's Law", "Define electric current", "Define electric potential difference", "Rearrange linear algebraic equations"],
    
    "Apply resistivity formula": ["Identify factors affecting resistance", "Rearrange linear algebraic equations"],
    
    "Calculate equivalent resistance in series": ["Apply Ohm's law to circuits"],
    "Calculate equivalent resistance in parallel": ["Apply Ohm's law to circuits", "Calculate inverse sums"],
    "Solve complex resistor networks": ["Calculate equivalent resistance in series", "Calculate equivalent resistance in parallel"],
    
    "Calculate heat generated by current": ["Apply Ohm's law to circuits"],
    "Apply electric power formulas": ["Calculate heat generated by current", "Apply power formula"],

    # CLASS 10 MAGNETIC EFFECTS
    "Apply Right-Hand Thumb Rule": ["Describe magnetic field lines", "Identify conventional current direction"],
    "Describe field of a solenoid": ["Describe magnetic field lines", "Apply Right-Hand Thumb Rule"],
    "Describe magnetic field of a circular loop": ["Describe magnetic field lines", "Apply Right-Hand Thumb Rule"],
    
    "Identify conditions for magnetic force": ["Apply F = ma", "Describe magnetic field lines", "Identify conventional current direction"],
    "Apply Fleming's Left-Hand Rule": ["Identify conditions for magnetic force"],
    
    "Explain role of a fuse": ["Calculate heat generated by current", "Distinguish live, neutral, and earth wires"]
}
```

## Counts
- **Total KCs:** 126
- **Per-Chapter KCs:**
  - Class 9 · Motion: 31
  - Class 9 · Force and Laws of Motion: 9
  - Class 9 · Gravitation: 14
  - Class 9 · Work and Energy: 13
  - Class 9 · Sound: 10
  - Class 10 · Light: 21
  - Class 10 · Electricity: 14
  - Class 10 · Eye: 6
  - Class 10 · Magnetic Effects: 8
- **Total Edges:** 139
- **Count of Class 9 → Class 10 cross-year edges:** 8

## Cross-year edge list
- Rearrange linear algebraic equations -> Cross-multiplication in proportions
- Read coordinates from a line graph -> Sign convention for coordinates
- Apply average speed formula -> Relate refractive index to speed of light
- Define work done by a constant force -> Define electric potential difference
- Rearrange linear algebraic equations -> Apply Ohm's law to circuits
- Rearrange linear algebraic equations -> Apply resistivity formula
- Apply power formula -> Apply electric power formulas
- Apply F = ma -> Identify conditions for magnetic force

## Exclusions
- **Structure of the human ear:** Excluded as it was generally rationalized out in current syllabi and is not highly predictive of other board physics concepts.
- **Electric motor and generator:** Omitted as they have been heavily reduced/removed in the rationalized editions in favor of core magnetic force/field logic.
- **Substitute u=0 or v=0:** Deemed a micro-skill in review. Absorbed implicitly when applying standard equations of motion.
- **"Numericals on light":** Rejected for being an umbrella KC. Replaced with granular components like `Apply mirror formula` and `Calculate linear magnification`.
- **Derivation of equations of motion:** Excluded because it's a long derivation sequence rarely tested as a distinct sub-skill compared to application logic.

## Self-review notes
1. **Grain adjustment (Equations of Motion):** The original idea of "Apply equations of motion" was too broad. Split it into three distinct KCs for each equation (`v=u+at`, `s=ut+1/2at^2`, `v^2-u^2=2as`) to ensure exact diagnostic precision.
2. **Edge correction (Average velocity):** "Calculate average velocity" initially depended on "Define average speed", but mathematically and conceptually, velocity logic diverges from speed logic. Updated it to only strictly depend on "Define velocity" to eliminate a forced non-essential dependency.
3. **Grain adjustment (Domestic Circuits):** "Domestic circuits" was overly broad as a single KC. I split it into identifying the three wires (live, neutral, earth) and explaining the practical role of a fuse, as they require distinct conceptual recall.
4. **Coverage Fixes:** During the critic review, I added orphaned exercise types like `Define relative density`, `Describe applications of multiple reflections of sound`, `Apply relative refractive index`, and `Describe magnetic field of a circular loop`.
5. **Edge Fixes (Vision Defects):** Initially, `Identify myopia` and `Identify hypermetropia` incorrectly depended on `Calculate power of a lens`. I corrected this by having identification stand alone, and making `Calculate power for vision correction` depend on identifying the defect.
6. **Grain Fixes (Concave Mirrors):** Split `Draw ray diagrams for concave mirrors` into `(real images)` and `(virtual image)` to reflect the pedagogical jump between the two types of image formations.
