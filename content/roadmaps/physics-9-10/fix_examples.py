import os, json

updates = {
    'apply-pressure-force-area': {
        'problem': "A woman weighing 500 N stands on one foot. The area of contact of her stiletto heel with the ground is 0.0001 m^2. Calculate the pressure exerted on the ground.",
        'steps': [
            {
                "narration": "Force seedha diya gaya hai kyunki weight 500 N hai.",
                "math": "F = 500 N"
            },
            {
                "narration": "Area pehle se hi square meters mein hai.",
                "math": "Area = 0.0001 m^2"
            },
            {
                "narration": "Formula Pressure = Force / Area lagayenge.",
                "math": "Pressure = 500 / 0.0001 = 5,000,000 Pa"
            }
        ],
        "answer": "5,000,000 Pa"
    },
    'apply-average-speed-formula': {
        'problem': "A migrating bird flies 120 km south in 4 hours, rests for 1 hour, and then flies another 80 km in 5 hours. What is its average speed for the entire trip?",
        'steps': [
            {
                "narration": "Total distance ke liye dono hisso ko add karenge.",
                "math": "Total Distance = 120 + 80 = 200 km"
            },
            {
                "narration": "Total time nikalte waqt rest wala time bhi count hoga.",
                "math": "Total Time = 4 + 1 + 5 = 10 hours"
            },
            {
                "narration": "Average speed nikalne ke liye total distance ko total time se divide karenge.",
                "math": "Average Speed = 200 / 10 = 20 km/h"
            }
        ],
        "answer": "20 km/h"
    },
    'apply-kinetic-energy-formula': {
        'problem': "An archer shoots an arrow of mass 0.2 kg with a velocity of 50 m/s. Calculate the kinetic energy of the arrow.",
        'steps': [
            {
                "narration": "Mass aur velocity diye gaye hain, units check karo.",
                "math": "m = 0.2 kg, v = 50 m/s"
            },
            {
                "narration": "Kinetic energy ka formula lagayenge.",
                "math": "KE = (1/2) * m * v^2"
            },
            {
                "narration": "Values rakh kar calculate karenge.",
                "math": "KE = 0.5 * 0.2 * 2500 = 250 J"
            }
        ],
        "answer": "250 J"
    },
    'apply-s-ut-1-2-at-2': {
        'problem': "An airplane touching down on a runway at 60 m/s applies reverse thrust, decelerating at 4 m/s^2. How far does it travel in 10 seconds?",
        'steps': [
            {
                "narration": "Initial velocity u = 60 m/s, deceleration hai to a = -4 m/s^2, aur time t = 10 s diya hai.",
                "math": "u = 60, a = -4, t = 10"
            },
            {
                "narration": "Second equation s = ut + (1/2)at^2 lagayenge.",
                "math": "s = (60 * 10) + (1/2 * (-4) * 10^2)"
            },
            {
                "narration": "Dono terms ko solve karke add karenge.",
                "math": "s = 600 + (-2 * 100) = 600 - 200 = 400"
            }
        ],
        "answer": "400 m"
    },
    'calculate-speed-in-circular-motion': {
        'problem': "A communication satellite orbits the Earth at a radius of 42000 km, taking 24 hours to complete one revolution. What is its speed in km/h?",
        'steps': [
            {
                "narration": "Radius aur time diya gaya hai.",
                "math": "r = 42000 km, t = 24 h"
            },
            {
                "narration": "Circular orbit ka total distance 2πr hota hai.",
                "math": "v = (2 * \\pi * 42000) / 24"
            },
            {
                "narration": "Pi ki value (3.14) rakh kar solve karenge.",
                "math": "v = 263893 / 24 \\approx 10995"
            }
        ],
        "answer": "10995 km/h"
    },
    'define-average-speed': {
        'problem': "A cheetah chases a prey for 200 m in 8 s, gets tired, and jogs the remaining 100 m in 22 s. Calculate its average speed.",
        'steps': [
            {
                "narration": "Pehle total distance calculate karte hain.",
                "math": "Total Distance = 200 + 100 = 300 m"
            },
            {
                "narration": "Phir total time dekhte hain.",
                "math": "Total Time = 8 + 22 = 30 s"
            },
            {
                "narration": "Total distance ko total time se divide kar denge.",
                "math": "Average Speed = 300 / 30 = 10 m/s"
            }
        ],
        "answer": "10 m/s"
    }
}

for slug, new_ex in updates.items():
    filepath = f"c:/Users/aloks/Desktop/RetainHQ/content/roadmaps/physics-9-10/{slug}.json"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep the diagram if there was one in the 2nd example
        old_ex = data['worked_example'][1]
        if 'diagram' in old_ex:
            new_ex['diagram'] = old_ex['diagram']
            
        data['worked_example'][1] = new_ex
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

print("Worked examples updated successfully.")
