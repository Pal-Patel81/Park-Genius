"""
Smart Parking System with AI Predictions
Handles user check-ins/check-outs and predicts availability
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle
import warnings
warnings.filterwarnings('ignore')

class ParkingLot:
    """Represents a single parking lot with capacity and current occupancy"""
    
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity
        self.current_occupancy = 0
        self.checked_in_users = {}  # {user_id: check_in_time}
        self.historical_data = []
        
    def check_in(self, user_id):
        """User checks in when they park"""
        if user_id not in self.checked_in_users:
            self.checked_in_users[user_id] = datetime.now()
            self.current_occupancy = min(self.current_occupancy + 1, self.capacity)
            return True
        return False
    
    def check_out(self, user_id):
        """User checks out when they leave"""
        if user_id in self.checked_in_users:
            check_in_time = self.checked_in_users.pop(user_id)
            duration = (datetime.now() - check_in_time).total_seconds() / 60  # minutes
            self.current_occupancy = max(self.current_occupancy - 1, 0)
            
            # Log historical data
            self.historical_data.append({
                'timestamp': datetime.now(),
                'occupancy': self.current_occupancy,
                'capacity': self.capacity,
                'duration': duration
            })
            return True
        return False
    
    def get_availability(self):
        """Returns current available spots"""
        return self.capacity - self.current_occupancy
    
    def get_occupancy_rate(self):
        """Returns current occupancy as percentage"""
        return (self.current_occupancy / self.capacity) * 100 if self.capacity > 0 else 0


class ParkingSystem:
    """Main system managing all parking lots"""
    
    def __init__(self):
        # Initialize all parking lots with their capacities
        self.lots = {
            'Lot A': ParkingLot('Lot A', 1049),
            'Lot C': ParkingLot('Lot C', 569),
            'Lot J': ParkingLot('Lot J', 211),
            'Lot K': ParkingLot('Lot K', 1493),
            'Lot L': ParkingLot('Lot L', 466),
            'Lot M': ParkingLot('Lot M', 152),
            'Lot O': ParkingLot('Lot O', 225),
            'Lot P': ParkingLot('Lot P', 217),
            'Carow Hall': ParkingLot('Carow Hall', 4),
            'PV Lot': ParkingLot('PV Lot', 141),
            'RAC/Banister Creek Court': ParkingLot('RAC/Banister Creek Court', 729),
            'Rapidan River Road': ParkingLot('Rapidan River Road', 209),
            'Townhouses': ParkingLot('Townhouses', 109),
            'West Campus Lot': ParkingLot('West Campus Lot', 543)
        }
        
        self.user_reliability_scores = {}  # Track how often users forget to check out
        self.ai_model = None
        
    def check_in(self, user_id, lot_name):
        """Handle user check-in"""
        if lot_name in self.lots:
            success = self.lots[lot_name].check_in(user_id)
            if success:
                print(f"✓ {user_id} checked in at {lot_name}")
                print(f"  Available spots: {self.lots[lot_name].get_availability()}/{self.lots[lot_name].capacity}")
                return True
            else:
                print(f"✗ {user_id} already checked in at {lot_name}")
                return False
        else:
            print(f"✗ Lot '{lot_name}' not found")
            return False
    
    def check_out(self, user_id, lot_name):
        """Handle user check-out"""
        if lot_name in self.lots:
            success = self.lots[lot_name].check_out(user_id)
            if success:
                print(f"✓ {user_id} checked out from {lot_name}")
                print(f"  Available spots: {self.lots[lot_name].get_availability()}/{self.lots[lot_name].capacity}")
                
                # Update reliability score (checked out properly)
                if user_id not in self.user_reliability_scores:
                    self.user_reliability_scores[user_id] = {'checkouts': 0, 'total': 0}
                self.user_reliability_scores[user_id]['checkouts'] += 1
                self.user_reliability_scores[user_id]['total'] += 1
                return True
            else:
                print(f"✗ {user_id} was not checked in at {lot_name}")
                return False
        else:
            print(f"✗ Lot '{lot_name}' not found")
            return False
    
    def auto_checkout_forgotten_users(self, lot_name, hours_threshold=3):
        """AI Feature: Automatically check out users who likely forgot (stayed > X hours)"""
        if lot_name not in self.lots:
            return
        
        lot = self.lots[lot_name]
        current_time = datetime.now()
        forgotten_users = []
        
        for user_id, check_in_time in list(lot.checked_in_users.items()):
            duration_hours = (current_time - check_in_time).total_seconds() / 3600
            
            if duration_hours > hours_threshold:
                forgotten_users.append(user_id)
                lot.check_out(user_id)
                
                # Update reliability score (forgot to check out)
                if user_id not in self.user_reliability_scores:
                    self.user_reliability_scores[user_id] = {'checkouts': 0, 'total': 0}
                self.user_reliability_scores[user_id]['total'] += 1
        
        if forgotten_users:
            print(f"\n🤖 AI Auto-checkout: {len(forgotten_users)} users at {lot_name}")
            print(f"   Users likely forgot to check out after {hours_threshold}+ hours")
    
    def get_all_availability(self):
        """Get current availability for all lots"""
        print("\n" + "="*70)
        print("CURRENT PARKING AVAILABILITY")
        print("="*70)
        
        for lot_name, lot in sorted(self.lots.items(), key=lambda x: x[1].get_availability(), reverse=True):
            available = lot.get_availability()
            occupancy_rate = lot.get_occupancy_rate()
            
            # Color coding based on availability
            if occupancy_rate < 50:
                status = "🟢 PLENTY"
            elif occupancy_rate < 80:
                status = "🟡 MODERATE"
            elif occupancy_rate < 95:
                status = "🟠 LIMITED"
            else:
                status = "🔴 FULL"
            
            print(f"{lot_name:30} {status:15} {available:4}/{lot.capacity:4} spots ({occupancy_rate:.1f}% full)")
        print("="*70 + "\n")
    
    def get_best_lots(self, top_n=5):
        """Get the top N lots with most availability"""
        sorted_lots = sorted(self.lots.items(), 
                           key=lambda x: x[1].get_availability(), 
                           reverse=True)
        
        print(f"\n🎯 TOP {top_n} LOTS WITH MOST AVAILABILITY:")
        print("-" * 50)
        for i, (lot_name, lot) in enumerate(sorted_lots[:top_n], 1):
            available = lot.get_availability()
            print(f"{i}. {lot_name}: {available} spots available")
        print()
    
    def generate_simulated_historical_data(self, days=30):
        """Generate simulated historical data for AI training"""
        print("\n📊 Generating simulated historical data for AI training...")
        
        data = []
        start_date = datetime.now() - timedelta(days=days)
        
        for lot_name, lot in self.lots.items():
            for day in range(days):
                current_date = start_date + timedelta(days=day)
                
                # Simulate hourly data
                for hour in range(24):
                    timestamp = current_date.replace(hour=hour, minute=0, second=0)
                    
                    # Simulate realistic patterns
                    day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
                    is_weekend = day_of_week >= 5
                    
                    # Base occupancy varies by time of day
                    if hour < 7:
                        base_rate = 0.1  # Very low at night
                    elif 7 <= hour < 9:
                        base_rate = 0.7  # Morning rush
                    elif 9 <= hour < 16:
                        base_rate = 0.85  # Peak day hours
                    elif 16 <= hour < 18:
                        base_rate = 0.6  # Late afternoon
                    else:
                        base_rate = 0.3  # Evening
                    
                    # Weekends are less busy
                    if is_weekend:
                        base_rate *= 0.4
                    
                    # Add some randomness
                    occupancy_rate = base_rate + np.random.normal(0, 0.1)
                    occupancy_rate = max(0, min(1, occupancy_rate))  # Keep between 0 and 1
                    
                    occupancy = int(lot.capacity * occupancy_rate)
                    
                    data.append({
                        'lot_name': lot_name,
                        'timestamp': timestamp,
                        'hour': hour,
                        'day_of_week': day_of_week,
                        'is_weekend': int(is_weekend),
                        'capacity': lot.capacity,
                        'occupancy': occupancy,
                        'occupancy_rate': occupancy_rate
                    })
        
        df = pd.DataFrame(data)
        print(f"✓ Generated {len(df)} data points across {days} days")
        return df
    
    def train_prediction_model(self, historical_df):
        """Train AI model to predict parking occupancy"""
        print("\n🤖 Training AI prediction model...")
        
        # Prepare features
        X = historical_df[['hour', 'day_of_week', 'is_weekend', 'capacity']]
        y = historical_df['occupancy']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train Random Forest model
        self.ai_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        self.ai_model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.ai_model.score(X_train, y_train)
        test_score = self.ai_model.score(X_test, y_test)
        
        print(f"✓ Model trained successfully!")
        print(f"  Training accuracy: {train_score:.2%}")
        print(f"  Testing accuracy: {test_score:.2%}")
        
        return self.ai_model
    
    def predict_availability(self, lot_name, hours_ahead=1):
        """AI Feature: Predict parking availability in X hours"""
        if self.ai_model is None:
            print("⚠ AI model not trained yet. Run train_prediction_model() first.")
            return None
        
        if lot_name not in self.lots:
            print(f"✗ Lot '{lot_name}' not found")
            return None
        
        lot = self.lots[lot_name]
        future_time = datetime.now() + timedelta(hours=hours_ahead)
        
        # Prepare features for prediction
        features = pd.DataFrame([{
            'hour': future_time.hour,
            'day_of_week': future_time.weekday(),
            'is_weekend': int(future_time.weekday() >= 5),
            'capacity': lot.capacity
        }])
        
        # Predict occupancy
        predicted_occupancy = int(self.ai_model.predict(features)[0])
        predicted_occupancy = max(0, min(predicted_occupancy, lot.capacity))
        predicted_available = lot.capacity - predicted_occupancy
        
        print(f"\n🔮 AI PREDICTION for {lot_name}")
        print(f"   Time: {future_time.strftime('%I:%M %p, %A')}")
        print(f"   Predicted available spots: {predicted_available}/{lot.capacity}")
        print(f"   Predicted occupancy: {(predicted_occupancy/lot.capacity)*100:.1f}%")
        
        return predicted_available
    
    def save_system(self, filename='parking_system_data.pkl'):
        """Save system state"""
        data = {
            'lots': self.lots,
            'user_reliability_scores': self.user_reliability_scores,
            'ai_model': self.ai_model
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print(f"✓ System saved to {filename}")
    
    def load_system(self, filename='parking_system_data.pkl'):
        """Load system state"""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            self.lots = data['lots']
            self.user_reliability_scores = data['user_reliability_scores']
            self.ai_model = data['ai_model']
            print(f"✓ System loaded from {filename}")
        except FileNotFoundError:
            print(f"✗ File {filename} not found")


def main():
    """Demo of the parking system"""
    print("="*70)
    print("SMART PARKING SYSTEM WITH AI")
    print("="*70)
    
    # Initialize system
    system = ParkingSystem()
    
    # Show initial availability
    system.get_all_availability()
    
    # Simulate some user activity
    print("\n--- SIMULATING USER ACTIVITY ---\n")
    system.check_in("student_001", "Lot K")
    system.check_in("student_002", "Lot K")
    system.check_in("student_003", "Lot A")
    system.check_in("student_004", "West Campus Lot")
    system.check_in("student_005", "Lot C")
    
    print("\n--- CURRENT STATUS ---")
    system.get_best_lots(top_n=3)
    
    # Check out some users
    print("\n--- USERS LEAVING ---\n")
    system.check_out("student_001", "Lot K")
    system.check_out("student_003", "Lot A")
    
    # Generate historical data and train AI model
    historical_data = system.generate_simulated_historical_data(days=30)
    system.train_prediction_model(historical_data)
    
    # Make predictions
    print("\n--- AI PREDICTIONS ---")
    system.predict_availability("Lot K", hours_ahead=2)
    system.predict_availability("West Campus Lot", hours_ahead=4)
    system.predict_availability("Lot A", hours_ahead=1)
    
    # Show final availability
    system.get_all_availability()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
