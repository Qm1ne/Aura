import random
from datetime import datetime, timedelta

class AuraDataGenerator:
    """Generates realistic health and calendar data with slight noise."""
    
    def __init__(self):
        # Baseline values
        self.base_hr = 70
        self.base_stress = 40
        self.meetings = [
            "Project Sync",
            "Client Presentation",
            "Morning Coffee with Team",
            "Architecture Review",
            "Deep Work Session",
            "Gym Session"
        ]

    async def get_vitals(self):
        """Returns HR and Stress with slight noise."""
        hr = self.base_hr + random.randint(-5, 5)
        stress = self.base_stress + random.randint(-10, 10)
        hr = max(50, min(180, hr))
        stress = max(0, min(100, stress))
        return {
            "heart_rate": hr,
            "stress_level": stress,
            "spo2": random.randint(96, 99),
            "timestamp": datetime.now().isoformat()
        }

    async def get_sleep_data(self):
        """Returns sleep metrics with slight noise."""
        score = 75 + random.randint(-15, 15)
        deep_sleep = round(1.5 + random.uniform(-0.5, 1.0), 1)
        return {
            "sleep_score": max(0, min(100, score)),
            "deep_sleep_hours": max(0, deep_sleep),
            "efficiency": f"{random.randint(85, 98)}%"
        }

    async def get_calendar(self):
        """Returns a list of 2-3 random meetings from the pool."""
        count = random.randint(2, 3)
        daily_meetings = random.sample(self.meetings, count)
        return {"meetings": daily_meetings}

    async def get_emergency_vitals(self):
        """Simulates a critical heart stroke/emergency state."""
        return {
            "heart_rate": 195,
            "blood_pressure": "210/120",
            "spo2": 82,
            "location": {"lat": 48.8584, "lng": 2.2945, "address": "Champ de Mars, Paris, France"},
            "status": "CRITICAL_SPIKE",
            "timestamp": datetime.now().isoformat()
        }

# Global generator instance
generator = AuraDataGenerator()
