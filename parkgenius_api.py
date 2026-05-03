"""
ParkGenius Enhanced API - Revolutionary Parking System
Includes: AI predictions, carpool matching, gamification, real-time updates
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from parking_system import ParkingSystem
from datetime import datetime, timedelta
import threading
import time
import random
import json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize parking system
parking_system = ParkingSystem()

# Enhanced user database (in production, use PostgreSQL)
users_db = {}
carpool_matches = []
achievements_db = {}

# Gamification system
ACHIEVEMENTS = {
    'perfect_week': {'name': 'Perfect Week', 'emoji': '🏆', 'requirement': 'Check out properly for 7 days straight'},
    'early_bird': {'name': 'Early Bird', 'emoji': '🌟', 'requirement': 'Park before 8am 10 times'},
    'carpool_pro': {'name': 'Carpool Pro', 'emoji': '🚗', 'requirement': 'Complete 5 carpools'},
    'spot_master': {'name': 'Spot Master', 'emoji': '🎯', 'requirement': 'Use app 50 times'},
    'eco_hero': {'name': 'Eco Hero', 'emoji': '🌍', 'requirement': 'Save 100 lbs of CO2'},
    'vip_status': {'name': 'VIP Status', 'emoji': '💎', 'requirement': 'Maintain 95%+ reliability for 30 days'}
}

# Initialize AI model
print("🚀 Initializing ParkGenius AI Engine...")
historical_data = parking_system.generate_simulated_historical_data(days=30)
parking_system.train_prediction_model(historical_data)
print("✅ AI Engine Ready!")


# ===============================
# CORE PARKING ENDPOINTS
# ===============================

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'app': 'ParkGenius',
        'version': '2.0',
        'tagline': 'Smart Parking, Smarter Campus',
        'features': [
            'Real-time availability',
            'AI predictions',
            'Carpool matching',
            'Gamification',
            'Social features',
            'AR navigation (coming soon)'
        ]
    })


@app.route('/lots', methods=['GET'])
def get_all_lots():
    """Enhanced lot data with predictions and social info"""
    lots_data = []
    
    for lot_name, lot in parking_system.lots.items():
        available = lot.get_availability()
        occupancy_rate = lot.get_occupancy_rate()
        
        # Get prediction for next hour
        predicted_available = predict_availability_internal(lot_name, 1)
        
        # Determine status
        if occupancy_rate < 50:
            status = "plenty"
            color = "#00FF88"
        elif occupancy_rate < 75:
            status = "moderate"
            color = "#FFD700"
        elif occupancy_rate < 90:
            status = "limited"
            color = "#FF6B35"
        else:
            status = "full"
            color = "#FF0080"
        
        # Count friends parked here (simulated)
        friends_here = random.randint(0, 3)
        
        lots_data.append({
            'name': lot_name,
            'capacity': lot.capacity,
            'available': available,
            'occupied': lot.current_occupancy,
            'occupancy_rate': round(occupancy_rate, 1),
            'status': status,
            'color': color,
            'predicted_1hr': predicted_available,
            'friends_here': friends_here,
            'walking_time_to_main': random.randint(2, 8)  # minutes
        })
    
    lots_data.sort(key=lambda x: x['available'], reverse=True)
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'total_lots': len(lots_data),
        'lots': lots_data,
        'campus_stats': {
            'total_available': sum(l['available'] for l in lots_data),
            'total_capacity': sum(l['capacity'] for l in lots_data),
            'avg_occupancy': round(sum(l['occupancy_rate'] for l in lots_data) / len(lots_data), 1)
        }
    })


@app.route('/checkin', methods=['POST'])
def check_in():
    """Enhanced check-in with gamification"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'lot_name' not in data:
        return jsonify({'success': False, 'error': 'Missing user_id or lot_name'}), 400
    
    user_id = data['user_id']
    lot_name = data['lot_name']
    
    if lot_name not in parking_system.lots:
        return jsonify({'success': False, 'error': f'Lot "{lot_name}" not found'}), 404
    
    # Initialize user if new
    if user_id not in users_db:
        users_db[user_id] = {
            'total_parks': 0,
            'streak': 0,
            'carbon_saved': 0,
            'time_saved': 0,
            'reliability_score': 100,
            'achievements': [],
            'last_checkin': None
        }
    
    success = parking_system.lots[lot_name].check_in(user_id)
    
    if success:
        users_db[user_id]['total_parks'] += 1
        users_db[user_id]['last_checkin'] = datetime.now().isoformat()
        
        # Broadcast to WebSocket clients
        socketio.emit('lot_update', {
            'lot_name': lot_name,
            'available': parking_system.lots[lot_name].get_availability()
        })
        
        lot = parking_system.lots[lot_name]
        return jsonify({
            'success': True,
            'message': f'Checked in to {lot_name}',
            'lot': {
                'name': lot_name,
                'available': lot.get_availability(),
                'capacity': lot.capacity,
                'occupancy_rate': round(lot.get_occupancy_rate(), 1)
            },
            'user_stats': users_db[user_id]
        })
    else:
        return jsonify({
            'success': False,
            'error': f'User already checked in to {lot_name}'
        }), 400


@app.route('/checkout', methods=['POST'])
def check_out():
    """Enhanced check-out with gamification updates"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'lot_name' not in data:
        return jsonify({'success': False, 'error': 'Missing user_id or lot_name'}), 400
    
    user_id = data['user_id']
    lot_name = data['lot_name']
    
    if lot_name not in parking_system.lots:
        return jsonify({'success': False, 'error': f'Lot "{lot_name}" not found'}), 404
    
    success = parking_system.lots[lot_name].check_out(user_id)
    
    if success and user_id in users_db:
        # Update streak
        users_db[user_id]['streak'] += 1
        
        # Calculate rewards (simulated)
        time_saved = random.randint(4, 9)
        carbon_saved = round(random.uniform(0.3, 0.8), 1)
        
        users_db[user_id]['time_saved'] += time_saved
        users_db[user_id]['carbon_saved'] += carbon_saved
        
        # Check for achievement unlocks
        new_achievements = check_achievements(user_id)
        
        # Broadcast update
        socketio.emit('lot_update', {
            'lot_name': lot_name,
            'available': parking_system.lots[lot_name].get_availability()
        })
        
        lot = parking_system.lots[lot_name]
        return jsonify({
            'success': True,
            'message': f'Checked out from {lot_name}',
            'rewards': {
                'time_saved': time_saved,
                'carbon_saved': carbon_saved,
                'streak_maintained': True
            },
            'lot': {
                'name': lot_name,
                'available': lot.get_availability(),
                'capacity': lot.capacity
            },
            'new_achievements': new_achievements,
            'user_stats': users_db[user_id]
        })
    else:
        return jsonify({
            'success': False,
            'error': f'User not checked in to {lot_name}'
        }), 400


# ===============================
# AI & PREDICTION ENDPOINTS
# ===============================

def predict_availability_internal(lot_name, hours_ahead):
    """Internal prediction function"""
    if parking_system.ai_model is None or lot_name not in parking_system.lots:
        return None
    
    lot = parking_system.lots[lot_name]
    future_time = datetime.now() + timedelta(hours=hours_ahead)
    
    import pandas as pd
    features = pd.DataFrame([{
        'hour': future_time.hour,
        'day_of_week': future_time.weekday(),
        'is_weekend': int(future_time.weekday() >= 5),
        'capacity': lot.capacity
    }])
    
    predicted_occupancy = int(parking_system.ai_model.predict(features)[0])
    predicted_occupancy = max(0, min(predicted_occupancy, lot.capacity))
    return lot.capacity - predicted_occupancy


@app.route('/predict/<lot_name>', methods=['GET'])
def predict_lot(lot_name):
    """AI prediction with confidence intervals"""
    hours_ahead = request.args.get('hours_ahead', default=1, type=int)
    
    if lot_name not in parking_system.lots:
        return jsonify({'success': False, 'error': f'Lot "{lot_name}" not found'}), 404
    
    predicted_available = predict_availability_internal(lot_name, hours_ahead)
    
    if predicted_available is None:
        return jsonify({'success': False, 'error': 'Prediction unavailable'}), 500
    
    lot = parking_system.lots[lot_name]
    future_time = datetime.now() + timedelta(hours=hours_ahead)
    
    # Calculate confidence (simulated)
    confidence = random.randint(85, 96)
    
    return jsonify({
        'success': True,
        'prediction': {
            'lot_name': lot_name,
            'predicted_time': future_time.isoformat(),
            'hours_ahead': hours_ahead,
            'predicted_available': predicted_available,
            'predicted_occupied': lot.capacity - predicted_available,
            'predicted_occupancy_rate': round(((lot.capacity - predicted_available) / lot.capacity) * 100, 1),
            'capacity': lot.capacity,
            'current_available': lot.get_availability(),
            'confidence': confidence,
            'recommendation': 'Good choice!' if predicted_available > 100 else 'Consider alternatives'
        }
    })


@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    """Natural language parking assistant"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'success': False, 'error': 'Missing message'}), 400
    
    message = data['message'].lower()
    user_id = data.get('user_id', 'anonymous')
    
    # Simple NLP-style response (in production, use GPT/Claude)
    response = ""
    
    if 'library' in message or 'near library' in message:
        response = "Based on your query, I recommend **Lot C** (5 min walk to library). Currently has **124 spots available** and predicted to have **98 spots** when you arrive. Alternatively, **West Campus Lot** is 7 min away with **131 spots**."
    
    elif 'close' in message or 'nearest' in message:
        response = "The closest lots to Main Building are: **Lot A** (2 min walk, 226 spots), **Lot K** (4 min walk, 637 spots), and **Lot M** (3 min walk, 14 spots). I recommend **Lot K** for best availability."
    
    elif 'carpool' in message or 'ride' in message:
        response = "Great! I found **3 carpool matches** for your schedule. Sarah (94% match) goes to West Campus MWF 10am-2pm. Mike (87% match) heads to Engineering TTh 1pm-5pm. Would you like to connect?"
    
    elif 'tonight' in message or 'event' in message:
        response = "There's a basketball game tonight at 7pm. Lots will fill up by 6pm. I recommend arriving by **5:30pm** and parking at **RAC/Banister** (usually less busy for events). I've set a reminder for you!"
    
    else:
        # Default intelligent response
        best_lot = sorted(parking_system.lots.items(), 
                         key=lambda x: x[1].get_availability(), 
                         reverse=True)[0]
        response = f"Based on current conditions, I recommend **{best_lot[0]}** with **{best_lot[1].get_availability()} spots available**. It typically takes 3-5 minutes to find a spot there. Would you like me to navigate you there?"
    
    return jsonify({
        'success': True,
        'response': response,
        'timestamp': datetime.now().isoformat(),
        'suggestions': [
            'Show me best available lots',
            'Find carpool matches',
            'Predict availability for 3pm'
        ]
    })


# ===============================
# CARPOOL MATCHING
# ===============================

@app.route('/carpool/profiles', methods=['GET'])
def get_carpool_profiles():
    """Get carpool match suggestions"""
    user_id = request.args.get('user_id')
    
    # Simulated carpool profiles (in production, query from DB with ML matching)
    profiles = [
        {
            'id': 'user_sarah_001',
            'name': 'Sarah Johnson',
            'schedule': 'MWF 10am-2pm',
            'route': 'West Campus → Main Building',
            'match_score': 94,
            'music_preference': 'Indie Pop',
            'verified': True,
            'reliability_score': 98,
            'carpools_completed': 23,
            'bio': 'Junior studying CS, love podcasts during rides!',
            'preferences': {
                'non_smoker': True,
                'punctual': True,
                'conversation_level': 'moderate'
            }
        },
        {
            'id': 'user_mike_002',
            'name': 'Mike Chen',
            'schedule': 'TTh 1pm-5pm',
            'route': 'Downtown → Engineering',
            'match_score': 87,
            'music_preference': 'Rock/Alternative',
            'verified': True,
            'reliability_score': 95,
            'carpools_completed': 18,
            'bio': 'Always early, hate being late. Let\'s save the planet!',
            'preferences': {
                'non_smoker': True,
                'punctual': True,
                'conversation_level': 'high'
            }
        },
        {
            'id': 'user_emma_003',
            'name': 'Emma Davis',
            'schedule': 'MWF 9am-1pm',
            'route': 'North Side → Library',
            'match_score': 92,
            'music_preference': 'Classical/Jazz',
            'verified': True,
            'reliability_score': 99,
            'carpools_completed': 31,
            'bio': 'Quiet rides preferred, studying during commute',
            'preferences': {
                'non_smoker': True,
                'punctual': True,
                'conversation_level': 'low'
            }
        }
    ]
    
    return jsonify({
        'success': True,
        'matches': profiles,
        'total_matches': len(profiles)
    })


@app.route('/carpool/match', methods=['POST'])
def create_carpool_match():
    """Match two users for carpooling"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'match_id' not in data:
        return jsonify({'success': False, 'error': 'Missing user_id or match_id'}), 400
    
    # Create match (in production, store in DB)
    match = {
        'id': f"match_{random.randint(1000, 9999)}",
        'users': [data['user_id'], data['match_id']],
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'route': 'To be determined',
        'next_ride': None
    }
    
    carpool_matches.append(match)
    
    # Update user carbon savings (they're carpooling!)
    if data['user_id'] in users_db:
        users_db[data['user_id']]['carbon_saved'] += 2.5  # Estimated per carpool
    
    return jsonify({
        'success': True,
        'match': match,
        'message': 'Match request sent! They\'ll be notified.',
        'estimated_savings': {
            'carbon_per_ride': '2.5 lbs CO2',
            'cost_per_ride': '$3.50',
            'time_social': 'Meet a new friend!'
        }
    })


# ===============================
# GAMIFICATION
# ===============================

def check_achievements(user_id):
    """Check if user unlocked any new achievements"""
    if user_id not in users_db:
        return []
    
    user = users_db[user_id]
    new_achievements = []
    
    # Perfect Week
    if user['streak'] >= 7 and 'perfect_week' not in user.get('achievements', []):
        user['achievements'].append('perfect_week')
        new_achievements.append(ACHIEVEMENTS['perfect_week'])
    
    # Eco Hero
    if user['carbon_saved'] >= 100 and 'eco_hero' not in user.get('achievements', []):
        user['achievements'].append('eco_hero')
        new_achievements.append(ACHIEVEMENTS['eco_hero'])
    
    # Spot Master
    if user['total_parks'] >= 50 and 'spot_master' not in user.get('achievements', []):
        user['achievements'].append('spot_master')
        new_achievements.append(ACHIEVEMENTS['spot_master'])
    
    return new_achievements


@app.route('/user/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Get comprehensive user statistics and achievements"""
    if user_id not in users_db:
        return jsonify({
            'success': True,
            'user_id': user_id,
            'stats': {
                'streak': 0,
                'total_parks': 0,
                'carbon_saved': 0,
                'time_saved': 0,
                'reliability_score': 100
            },
            'achievements': [],
            'rank': 'Beginner'
        })
    
    user = users_db[user_id]
    
    # Calculate rank
    total_points = user['total_parks'] * 10 + user['streak'] * 50 + len(user.get('achievements', [])) * 100
    if total_points > 1000:
        rank = 'Legend'
    elif total_points > 500:
        rank = 'Master'
    elif total_points > 200:
        rank = 'Expert'
    elif total_points > 50:
        rank = 'Intermediate'
    else:
        rank = 'Beginner'
    
    # Get achievement details
    user_achievements = []
    for ach_id in user.get('achievements', []):
        if ach_id in ACHIEVEMENTS:
            user_achievements.append(ACHIEVEMENTS[ach_id])
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'stats': {
            'streak': user['streak'],
            'total_parks': user['total_parks'],
            'carbon_saved': round(user['carbon_saved'], 1),
            'time_saved': user['time_saved'],
            'reliability_score': user['reliability_score']
        },
        'achievements': user_achievements,
        'rank': rank,
        'total_points': total_points,
        'next_achievement': get_next_achievement(user)
    })


def get_next_achievement(user):
    """Get the next achievement user can unlock"""
    if user['streak'] < 7:
        return {'name': 'Perfect Week', 'progress': user['streak'], 'requirement': 7}
    elif user['carbon_saved'] < 100:
        return {'name': 'Eco Hero', 'progress': round(user['carbon_saved'], 1), 'requirement': 100}
    elif user['total_parks'] < 50:
        return {'name': 'Spot Master', 'progress': user['total_parks'], 'requirement': 50}
    return None


@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top users by various metrics"""
    metric = request.args.get('metric', 'total_points')
    limit = request.args.get('limit', default=10, type=int)
    
    # Calculate rankings (simulated with real users + fake ones)
    leaderboard = []
    
    for user_id, user_data in users_db.items():
        total_points = user_data['total_parks'] * 10 + user_data['streak'] * 50
        leaderboard.append({
            'user_id': user_id,
            'name': f"User {user_id[-4:]}",
            'streak': user_data['streak'],
            'carbon_saved': user_data['carbon_saved'],
            'time_saved': user_data['time_saved'],
            'total_points': total_points,
            'reliability': user_data['reliability_score']
        })
    
    # Add some fake users for demo
    for i in range(10):
        leaderboard.append({
            'user_id': f'demo_user_{i}',
            'name': f'Demo User {i+1}',
            'streak': random.randint(1, 30),
            'carbon_saved': round(random.uniform(5, 200), 1),
            'time_saved': random.randint(20, 500),
            'total_points': random.randint(100, 2000),
            'reliability': random.randint(85, 100)
        })
    
    # Sort by metric
    if metric == 'streak':
        leaderboard.sort(key=lambda x: x['streak'], reverse=True)
    elif metric == 'carbon_saved':
        leaderboard.sort(key=lambda x: x['carbon_saved'], reverse=True)
    else:
        leaderboard.sort(key=lambda x: x['total_points'], reverse=True)
    
    return jsonify({
        'success': True,
        'leaderboard': leaderboard[:limit],
        'metric': metric,
        'updated_at': datetime.now().isoformat()
    })


# ===============================
# WEBSOCKET FOR REAL-TIME UPDATES
# ===============================

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'status': 'connected', 'message': 'Welcome to ParkGenius real-time updates!'})


@socketio.on('subscribe_lot')
def handle_subscribe(data):
    """Subscribe to updates for a specific lot"""
    lot_name = data.get('lot_name')
    if lot_name in parking_system.lots:
        join_room(lot_name)
        emit('subscribed', {'lot_name': lot_name, 'message': f'Subscribed to {lot_name} updates'})


@socketio.on('unsubscribe_lot')
def handle_unsubscribe(data):
    """Unsubscribe from lot updates"""
    lot_name = data.get('lot_name')
    leave_room(lot_name)
    emit('unsubscribed', {'lot_name': lot_name})


# ===============================
# BACKGROUND TASKS
# ===============================

def auto_checkout_background():
    """Background task to auto-checkout forgotten users"""
    while True:
        time.sleep(3600)  # Run every hour
        for lot_name in parking_system.lots.keys():
            parking_system.auto_checkout_forgotten_users(lot_name, hours_threshold=3)


# Start background thread
background_thread = threading.Thread(target=auto_checkout_background, daemon=True)
background_thread.start()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 PARKGENIUS API SERVER v2.0")
    print("="*70)
    print("Features: AI Predictions | Carpool Matching | Gamification | Real-time")
    print("Server starting on http://localhost:5001")
    print("="*70 + "\n")

    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
