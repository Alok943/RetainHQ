import os, json

updates = {
    'apply-electric-power-formulas': {
        'rq1': {'q': 'What is the formula for electric power in terms of resistance and current?', 'a': 'P = I²R'},
        'rq2': {'q': 'What is the relationship between power, voltage, and current?', 'a': 'P = V × I'},
        'oa': {'q': 'An electric heater is rated 1500 W. How much energy does it use in 10 hours?', 'a': '15 kWh', 'approach': 'Energy = Power × time = 1.5 kW × 10 h = 15 kWh.'}
    },
    'apply-equations-of-motion-for-free-fall': {
        'rq1': {'q': 'What is the acceleration of a freely falling object?', 'a': 'g = 9.8 m/s²'},
        'rq2': {'q': 'If an object is thrown upwards, what is its velocity at the highest point?', 'a': 'Zero'},
        'oa': {'q': 'A ball is dropped from a height of 20m. Find time to reach ground (g=10).', 'a': '2 s', 'approach': 'Use h = ut + 0.5gt². 20 = 0 + 5t² => t² = 4 => t = 2s.'}
    },
    'apply-flemings-left-hand-rule': {
        'rq1': {'q': 'Which finger represents the magnetic field in Fleming\'s Left Hand Rule?', 'a': 'The index finger'},
        'rq2': {'q': 'Which finger points in the direction of the current?', 'a': 'The middle finger'},
        'oa': {'q': 'If a positively charged alpha particle moves west and experiences an upward force, what is the direction of the magnetic field?', 'a': 'North', 'approach': 'Apply Fleming\'s Left-Hand Rule.'}
    },
    'apply-ohms-law-to-circuits': {
        'rq1': {'q': 'What happens to the current if the resistance is doubled and voltage is constant?', 'a': 'The current is halved.'},
        'rq2': {'q': 'What does a straight line on a V-I graph indicate?', 'a': 'The conductor follows Ohm\'s Law.'},
        'oa': {'q': 'Find the current if a 12V battery is connected to a 6Ω resistor.', 'a': '2 A', 'approach': 'I = V/R = 12 / 6 = 2 A.'}
    },
    'apply-pressure-force-area': {
        'rq1': {'q': 'What happens to pressure if the force is doubled over the same area?', 'a': 'Pressure doubles.'},
        'rq2': {'q': 'Why do school bags have wide straps?', 'a': 'To increase the area and reduce the pressure on shoulders.'},
        'oa': {'q': 'Calculate the pressure if a force of 100 N acts on an area of 2 m².', 'a': '50 Pa', 'approach': 'Pressure = Force / Area = 100 / 2 = 50 Pa.'}
    },
    'apply-resistivity-formula': {
        'rq1': {'q': 'Does resistivity depend on the length of the wire?', 'a': 'No, it depends only on the material and temperature.'},
        'rq2': {'q': 'What is the SI unit of resistivity?', 'a': 'Ohm-meter (Ω·m)'},
        'oa': {'q': 'A wire of resistance 10Ω is doubled in length. What happens to its resistivity?', 'a': 'Resistivity remains unchanged.', 'approach': 'Resistivity is a material property and does not change with physical dimensions like length.'}
    },
    'apply-right-hand-thumb-rule': {
        'rq1': {'q': 'What does the thumb represent in the right-hand thumb rule?', 'a': 'The direction of the current.'},
        'rq2': {'q': 'What do the curled fingers represent?', 'a': 'The direction of the magnetic field lines.'},
        'oa': {'q': 'A current flows vertically upwards. What is the direction of the magnetic field?', 'a': 'Anticlockwise', 'approach': 'Point your right thumb up, your fingers curl in an anticlockwise direction.'}
    },
    'calculate-equivalent-resistance-in-parallel': {
        'rq1': {'q': 'Is the equivalent resistance in parallel greater or less than the individual resistances?', 'a': 'Always less than the smallest individual resistance.'},
        'rq2': {'q': 'What remains constant across all resistors in a parallel circuit?', 'a': 'The potential difference (voltage).'},
        'oa': {'q': 'Calculate the equivalent resistance of two 4Ω resistors in parallel.', 'a': '2 Ω', 'approach': '1/Rp = 1/4 + 1/4 = 2/4 = 1/2. So Rp = 2 Ω.'}
    },
    'calculate-equivalent-resistance-in-series': {
        'rq1': {'q': 'What remains constant through all resistors in a series circuit?', 'a': 'The electric current.'},
        'rq2': {'q': 'How do you find equivalent resistance in a series circuit?', 'a': 'By adding the individual resistances (Rs = R1 + R2 + ...)'},
        'oa': {'q': 'Three resistors of 2Ω, 3Ω, and 5Ω are in series. Find the total resistance.', 'a': '10 Ω', 'approach': 'Rs = 2 + 3 + 5 = 10 Ω.'}
    },
    'calculate-heat-generated-by-current': {
        'rq1': {'q': 'What is Joule\'s Law of Heating equation?', 'a': 'H = I²Rt'},
        'rq2': {'q': 'What happens to heat generated if the current is doubled?', 'a': 'It increases by four times.'},
        'oa': {'q': '100 J of heat is produced each second in a 4Ω resistance. Find the potential difference across the resistor.', 'a': '20 V', 'approach': 'H = V²t/R => 100 = V²(1)/4 => V² = 400 => V = 20 V.'}
    },
    'calculate-inverse-sums': {
        'rq1': {'q': 'Why do we need inverse sums in physics?', 'a': 'To calculate equivalent resistance in parallel and apply lens/mirror formulas.'},
        'rq2': {'q': 'What is the sum of 1/2 and 1/2?', 'a': '1'},
        'oa': {'q': 'Solve for f: 1/f = 1/3 + 1/6', 'a': 'f = 2', 'approach': '1/3 + 1/6 = 2/6 + 1/6 = 3/6 = 1/2. Therefore, f = 2.'}
    },
    'calculate-power-for-vision-correction': {
        'rq1': {'q': 'What is the SI unit of power of a lens?', 'a': 'Dioptre (D)'},
        'rq2': {'q': 'Is the power of a concave lens positive or negative?', 'a': 'Negative'},
        'oa': {'q': 'A person uses a lens of power -2.0 D. What is the focal length?', 'a': '-50 cm', 'approach': 'f = 1/P = 1/(-2) = -0.5 m = -50 cm.'}
    },
    'calculate-weight-on-earth-and-moon': {
        'rq1': {'q': 'What is the relation between weight on the Moon and weight on Earth?', 'a': 'Weight on Moon is 1/6th of weight on Earth.'},
        'rq2': {'q': 'Does the mass of an object change on the Moon?', 'a': 'No, mass remains constant everywhere.'},
        'oa': {'q': 'An object weighs 60 N on Earth. What is its weight on the Moon?', 'a': '10 N', 'approach': 'Weight on Moon = 60 / 6 = 10 N.'}
    },
    'cross-multiplication-in-proportions': {
        'rq1': {'q': 'If a/b = c/d, what is the cross-multiplied form?', 'a': 'a × d = b × c'},
        'rq2': {'q': 'When is cross-multiplication most useful?', 'a': 'When solving for an unknown variable in a proportion.'},
        'oa': {'q': 'Solve for x: x/4 = 3/2', 'a': 'x = 6', 'approach': '2x = 12 => x = 6.'}
    },
    'define-buoyant-force': {
        'rq1': {'q': 'What is buoyant force?', 'a': 'The upward force exerted by a fluid on an immersed object.'},
        'rq2': {'q': 'What happens if buoyant force is less than the weight of the object?', 'a': 'The object sinks.'},
        'oa': {'q': 'Why does an iron nail sink while a cork floats?', 'a': 'Because the density of iron is more than water, so its weight exceeds buoyant force. Cork is less dense than water.', 'approach': 'Compare densities and buoyant forces.'}
    },
    'define-electric-current': {
        'rq1': {'q': 'What is electric current?', 'a': 'The rate of flow of electric charges.'},
        'rq2': {'q': 'What instrument measures electric current?', 'a': 'An ammeter.'},
        'oa': {'q': 'A current of 0.5 A is drawn by a filament for 10 minutes. Find the amount of electric charge.', 'a': '300 C', 'approach': 'Q = I × t = 0.5 A × 600 s = 300 C.'}
    },
    'define-electric-potential-difference': {
        'rq1': {'q': 'What is potential difference?', 'a': 'The work done to move a unit charge from one point to another.'},
        'rq2': {'q': 'What instrument measures potential difference?', 'a': 'A voltmeter.'},
        'oa': {'q': 'How much work is done in moving a charge of 2 C across two points having a potential difference 12 V?', 'a': '24 J', 'approach': 'W = V × Q = 12 V × 2 C = 24 J.'}
    },
    'define-free-fall': {
        'rq1': {'q': 'What is free fall?', 'a': 'When an object falls towards the earth under the sole influence of gravity.'},
        'rq2': {'q': 'Is acceleration constant during free fall near the earth\'s surface?', 'a': 'Yes, it is approximately 9.8 m/s².'},
        'oa': {'q': 'Does a heavier object fall faster than a lighter object in a vacuum?', 'a': 'No, they fall at the same rate.', 'approach': 'Acceleration due to gravity is independent of the object\'s mass.'}
    },
    'define-pressure': {
        'rq1': {'q': 'How does pressure depend on area?', 'a': 'Pressure is inversely proportional to the area.'},
        'rq2': {'q': 'What is pressure?', 'a': 'Force acting perpendicularly per unit area.'},
        'oa': {'q': 'Why are the tracks of a battle tank made so wide?', 'a': 'To increase the surface area and reduce the pressure on the ground.', 'approach': 'Relate wide area to decreased pressure using P = F/A.'}
    },
    'define-relative-density': {
        'rq1': {'q': 'What is relative density?', 'a': 'The ratio of the density of a substance to the density of water.'},
        'rq2': {'q': 'Does relative density have a unit?', 'a': 'No, it is a dimensionless ratio.'},
        'oa': {'q': 'The relative density of silver is 10.8. The density of water is 10³ kg/m³. What is the density of silver in SI unit?', 'a': '10.8 × 10³ kg/m³', 'approach': 'Density = Relative density × Density of water.'}
    },
    'define-thrust': {
        'rq1': {'q': 'What is thrust?', 'a': 'The force acting on an object perpendicular to its surface.'},
        'rq2': {'q': 'What is the SI unit of thrust?', 'a': 'Newton (N)'},
        'oa': {'q': 'If a block exerts a force of 50 N on a table, what is the thrust?', 'a': '50 N', 'approach': 'Thrust is simply the perpendicular force exerted, which is 50 N.'}
    },
    'describe-applications-of-multiple-reflections-of-sound': {
        'rq1': {'q': 'Give an example of a device based on multiple reflections of sound.', 'a': 'Megaphone or Stethoscope.'},
        'rq2': {'q': 'How does a stethoscope work?', 'a': 'Sound of the heart travels through the tube by multiple reflections.'},
        'oa': {'q': 'Why are the ceilings of concert halls curved?', 'a': 'So that sound after reflection reaches all corners of the hall.', 'approach': 'Explain that curved surfaces act as large sound reflectors.'}
    },
    'describe-field-of-a-solenoid': {
        'rq1': {'q': 'What is a solenoid?', 'a': 'A coil of many circular turns of insulated copper wire wrapped closely in the shape of a cylinder.'},
        'rq2': {'q': 'What does the magnetic field inside a solenoid look like?', 'a': 'Uniform, represented by parallel straight lines.'},
        'oa': {'q': 'How can you increase the magnetic field of a solenoid?', 'a': 'By increasing the current or the number of turns.', 'approach': 'State the factors affecting the magnetic field strength of a solenoid.'}
    },
    'describe-magnetic-field-lines': {
        'rq1': {'q': 'In which direction do magnetic field lines emerge?', 'a': 'From the North pole to the South pole outside the magnet.'},
        'rq2': {'q': 'Can two magnetic field lines intersect?', 'a': 'No, because if they did, the compass needle would point in two directions at the intersection.'},
        'oa': {'q': 'What does the degree of closeness of magnetic field lines indicate?', 'a': 'The relative strength of the magnetic field.', 'approach': 'Explain that denser lines mean stronger magnetic forces.'}
    },
    'describe-magnetic-field-of-a-circular-loop': {
        'rq1': {'q': 'What is the shape of the magnetic field lines near a circular loop carrying current?', 'a': 'Concentric circles.'},
        'rq2': {'q': 'What happens to the magnetic field at the center of the loop if current is increased?', 'a': 'The magnetic field strength increases.'},
        'oa': {'q': 'How is the magnetic field at the center of a circular coil related to its radius?', 'a': 'It is inversely proportional to the radius of the coil.', 'approach': 'Use the relationship B ∝ 1/r.'}
    },
    'determine-if-an-object-floats-or-sinks': {
        'rq1': {'q': 'What is the condition for an object to float?', 'a': 'Its density must be less than or equal to the density of the fluid.'},
        'rq2': {'q': 'What happens if an object is denser than water?', 'a': 'It will sink.'},
        'oa': {'q': 'An object has a density of 0.8 g/cm³. Will it float or sink in water (density 1 g/cm³)?', 'a': 'It will float.', 'approach': 'Since 0.8 < 1.0, the object\'s density is lower than water, so it floats.'}
    },
    'distinguish-live-neutral-and-earth-wires': {
        'rq1': {'q': 'What is the typical color of the earth wire insulation?', 'a': 'Green'},
        'rq2': {'q': 'What is the purpose of the earth wire?', 'a': 'To provide a low-resistance path to the ground, preventing electric shocks.'},
        'oa': {'q': 'What is the potential difference between the live wire and the neutral wire in India?', 'a': '220 V', 'approach': 'State the standard AC voltage supplied to households.'}
    },
    'distinguish-mass-and-weight': {
        'rq1': {'q': 'Which quantity remains constant throughout the universe, mass or weight?', 'a': 'Mass'},
        'rq2': {'q': 'What is the SI unit of mass and weight?', 'a': 'Mass is kg, Weight is Newton (N).'},
        'oa': {'q': 'Can the weight of an object be zero?', 'a': 'Yes, in deep space or during free fall where g = 0.', 'approach': 'Weight is mg, so if gravity is zero, weight is zero, but mass is not.'}
    },
    'explain-blue-color-of-sky': {
        'rq1': {'q': 'Which phenomenon causes the sky to appear blue?', 'a': 'Scattering of light by atmospheric particles.'},
        'rq2': {'q': 'Which color of light scatters the most?', 'a': 'Blue (shorter wavelengths).'},
        'oa': {'q': 'Why does the sky appear dark to an astronaut?', 'a': 'Because there is no atmosphere in space to scatter sunlight.', 'approach': 'Link the presence of an atmosphere to the scattering effect.'}
    },
    'explain-role-of-a-fuse': {
        'rq1': {'q': 'What is a fuse?', 'a': 'A safety device that breaks the circuit if the current exceeds a safe limit.'},
        'rq2': {'q': 'Is a fuse connected in series or parallel with the live wire?', 'a': 'In series.'},
        'oa': {'q': 'How does a fuse protect an electrical appliance?', 'a': 'It melts due to Joule heating when excessive current flows, breaking the circuit.', 'approach': 'Explain the heating effect of electric current (H=I²Rt).'}
    },
    'explain-twinkling-of-stars': {
        'rq1': {'q': 'What causes the twinkling of stars?', 'a': 'Atmospheric refraction of starlight.'},
        'rq2': {'q': 'Why don\'t planets twinkle?', 'a': 'Because they are closer to Earth and act as extended sources of light, nullifying the twinkling effect.'},
        'oa': {'q': 'Explain how the continuous changing of the Earth\'s atmosphere affects starlight.', 'a': 'It causes the apparent position of the star to fluctuate and the amount of light entering the eye to vary, leading to twinkling.', 'approach': 'Describe the effect of varying refractive indices in the atmosphere.'}
    },
    'identify-conditions-for-magnetic-force': {
        'rq1': {'q': 'When does a current-carrying conductor experience maximum magnetic force?', 'a': 'When the current direction is perpendicular to the magnetic field.'},
        'rq2': {'q': 'When is the magnetic force on a conductor zero?', 'a': 'When the conductor is parallel to the magnetic field.'},
        'oa': {'q': 'An electron enters a magnetic field parallel to the field lines. What force does it experience?', 'a': 'Zero force.', 'approach': 'Force is zero when the angle between velocity and magnetic field is 0 or 180 degrees.'}
    },
    'identify-conventional-current-direction': {
        'rq1': {'q': 'What is the conventional direction of electric current?', 'a': 'From the positive terminal to the negative terminal.'},
        'rq2': {'q': 'In which direction do electrons actually flow in a circuit?', 'a': 'From the negative terminal to the positive terminal.'},
        'oa': {'q': 'If a beam of protons moves towards the East, what is the direction of the conventional current?', 'a': 'East', 'approach': 'Conventional current follows the direction of positive charge flow.'}
    },
    'identify-factors-affecting-resistance': {
        'rq1': {'q': 'How does resistance depend on the length of a wire?', 'a': 'It is directly proportional (R ∝ L).'},
        'rq2': {'q': 'How does resistance depend on the cross-sectional area?', 'a': 'It is inversely proportional (R ∝ 1/A).'},
        'oa': {'q': 'If a wire is stretched to double its length without changing its volume, what happens to its resistance?', 'a': 'It becomes four times the original resistance.', 'approach': 'Length doubles, area halves, so R = ρ(2L)/(A/2) = 4ρL/A.'}
    },
    'identify-hypermetropia-far-sightedness': {
        'rq1': {'q': 'What is hypermetropia?', 'a': 'A defect where a person can see distant objects clearly but cannot see nearby objects distinctly.'},
        'rq2': {'q': 'Which lens is used to correct hypermetropia?', 'a': 'A convex lens.'},
        'oa': {'q': 'Where is the image of a nearby object formed in a hypermetropic eye?', 'a': 'Behind the retina.', 'approach': 'Explain that the lens converging power is too low.'}
    },
    'identify-myopia-near-sightedness': {
        'rq1': {'q': 'What is myopia?', 'a': 'A defect where a person can see nearby objects clearly but cannot see distant objects distinctly.'},
        'rq2': {'q': 'Which lens is used to correct myopia?', 'a': 'A concave lens.'},
        'oa': {'q': 'Where is the image of a distant object formed in a myopic eye?', 'a': 'In front of the retina.', 'approach': 'Explain that the eye lens is too converging or the eyeball is too long.'}
    },
    'identify-symbols-in-a-circuit-diagram': {
        'rq1': {'q': 'What does a straight line represent in a circuit diagram?', 'a': 'A connecting wire.'},
        'rq2': {'q': 'What is the symbol for a resistor?', 'a': 'A zigzag line.'},
        'oa': {'q': 'How is an ammeter connected in a circuit and what is its symbol?', 'a': 'It is connected in series and represented by an \'A\' enclosed in a circle.', 'approach': 'Identify the series connection rule for ammeters.'}
    },
    'sign-convention-for-coordinates': {
        'rq1': {'q': 'What is the sign of distance measured to the right of the origin?', 'a': 'Positive.'},
        'rq2': {'q': 'What is the sign of height measured downwards from the principal axis?', 'a': 'Negative.'},
        'oa': {'q': 'If an object is placed 20 cm in front of a mirror, what is its object distance according to sign convention?', 'a': '-20 cm', 'approach': 'The object is always placed to the left of the mirror, so it is negative.'}
    },
    'solve-complex-resistor-networks': {
        'rq1': {'q': 'What is the first step in solving a complex resistor network?', 'a': 'Identify which resistors are purely in series or purely in parallel.'},
        'rq2': {'q': 'How do you simplify a series-parallel combination?', 'a': 'Solve the simplest inner branches first and replace them with their equivalent resistance.'},
        'oa': {'q': 'Two 2Ω resistors in parallel are connected in series with a 3Ω resistor. What is the total resistance?', 'a': '4 Ω', 'approach': 'Parallel part: 1Ω. Total = 1 + 3 = 4Ω.'}
    },
    'state-acceleration-due-to-gravity-g': {
        'rq1': {'q': 'What is the standard value of acceleration due to gravity (g) on Earth?', 'a': '9.8 m/s²'},
        'rq2': {'q': 'Does the value of g remain exactly the same everywhere on Earth?', 'a': 'No, it is slightly greater at the poles than at the equator.'},
        'oa': {'q': 'Why is the value of g greater at the poles than at the equator?', 'a': 'Because the Earth is an oblate spheroid, making the poles closer to the center of the Earth.', 'approach': 'Use g = GM/R² and relate it to the Earth\'s radius.'}
    },
    'state-archimedes-principle': {
        'rq1': {'q': 'What is Archimedes\' Principle?', 'a': 'When an object is immersed in a fluid, it experiences an upward force equal to the weight of the fluid displaced by it.'},
        'rq2': {'q': 'What is the upward force called?', 'a': 'Buoyant force.'},
        'oa': {'q': 'How do submarines use Archimedes\' principle to dive?', 'a': 'By filling their ballast tanks with water to increase their average density.', 'approach': 'Explain that when weight exceeds the buoyant force of displaced water, the submarine dives.'}
    },
    'state-laws-of-reflection-of-sound': {
        'rq1': {'q': 'What is the first law of reflection of sound?', 'a': 'The angle of incidence is equal to the angle of reflection.'},
        'rq2': {'q': 'What is the second law of reflection of sound?', 'a': 'The incident sound wave, the reflected sound wave, and the normal at the point of incidence lie in the same plane.'},
        'oa': {'q': 'Does sound follow the same laws of reflection as light?', 'a': 'Yes, sound waves reflect off surfaces just like light waves do.', 'approach': 'Compare the behavior of sound waves with light waves.'}
    },
    'state-ohms-law': {
        'rq1': {'q': 'What does Ohm\'s law state?', 'a': 'The potential difference across a conductor is directly proportional to the current through it, provided temperature is constant.'},
        'rq2': {'q': 'What is the mathematical form of Ohm\'s law?', 'a': 'V = IR'},
        'oa': {'q': 'Why does Ohm\'s law fail if the temperature of the conductor changes?', 'a': 'Because a change in temperature changes the resistance of the material.', 'approach': 'Highlight that Ohm\'s law assumes constant physical conditions like temperature.'}
    }
}

path = 'c:/Users/aloks/Desktop/RetainHQ/content/roadmaps/physics-9-10'

for filename in os.listdir(path):
    if not filename.endswith('.json'):
        continue
    filepath = os.path.join(path, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    slug = data.get('slug')
    changed = False
    
    if slug in updates:
        for rq in data.get('recall_questions', []):
            if 'Extra recall' in rq.get('q', ''):
                if 'Variant' in rq['q']:
                    rq['q'] = updates[slug]['rq2']['q']
                    rq['answer'] = updates[slug]['rq2']['a']
                else:
                    rq['q'] = updates[slug]['rq1']['q']
                    rq['answer'] = updates[slug]['rq1']['a']
                changed = True
                
        for oa in data.get('oa_questions', []):
            if 'Extra OA' in oa.get('question', ''):
                oa['question'] = updates[slug]['oa']['q']
                oa['answer'] = updates[slug]['oa']['a']
                oa['approach'] = updates[slug]['oa']['approach']
                changed = True
                
    # Also fix diagram issues if any empty forces array for free-body
    if data.get('diagram', {}).get('type') == 'free-body':
        if 'object' not in data['diagram']:
            data['diagram']['object'] = 'box'
            changed = True
        if 'forces' not in data['diagram']:
            data['diagram']['forces'] = []
            changed = True
            
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

print("Placeholders updated successfully.")
