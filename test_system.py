"""
Test script to verify the Smart Parking System works correctly
"""

from parking_system import ParkingSystem
import time

def test_basic_functionality():
    """Test basic check-in/check-out functionality"""
    print("\n" + "="*70)
    print("TEST 1: BASIC CHECK-IN/CHECK-OUT")
    print("="*70)
    
    system = ParkingSystem()
    
    # Test check-in
    print("\n1. Testing check-in...")
    assert system.check_in("test_user_1", "Lot K") == True
    print("✓ Check-in successful")
    
    # Test duplicate check-in
    print("\n2. Testing duplicate check-in (should fail)...")
    assert system.check_in("test_user_1", "Lot K") == False
    print("✓ Duplicate check-in correctly rejected")
    
    # Test check-out
    print("\n3. Testing check-out...")
    assert system.check_out("test_user_1", "Lot K") == True
    print("✓ Check-out successful")
    
    # Test invalid check-out
    print("\n4. Testing invalid check-out (should fail)...")
    assert system.check_out("test_user_1", "Lot K") == False
    print("✓ Invalid check-out correctly rejected")
    
    print("\n✅ All basic functionality tests PASSED\n")


def test_availability_tracking():
    """Test that availability is tracked correctly"""
    print("\n" + "="*70)
    print("TEST 2: AVAILABILITY TRACKING")
    print("="*70)
    
    system = ParkingSystem()
    
    lot_k = system.lots["Lot K"]
    initial_available = lot_k.get_availability()
    print(f"\nInitial availability: {initial_available}")
    
    # Check in 5 users
    print("\n1. Checking in 5 users...")
    for i in range(5):
        system.check_in(f"test_user_{i}", "Lot K")
    
    current_available = lot_k.get_availability()
    print(f"Current availability: {current_available}")
    assert current_available == initial_available - 5
    print("✓ Availability decreased correctly")
    
    # Check out 3 users
    print("\n2. Checking out 3 users...")
    for i in range(3):
        system.check_out(f"test_user_{i}", "Lot K")
    
    final_available = lot_k.get_availability()
    print(f"Final availability: {final_available}")
    assert final_available == initial_available - 2
    print("✓ Availability increased correctly after checkout")
    
    print("\n✅ All availability tracking tests PASSED\n")


def test_ai_prediction():
    """Test AI prediction functionality"""
    print("\n" + "="*70)
    print("TEST 3: AI PREDICTION MODEL")
    print("="*70)
    
    system = ParkingSystem()
    
    # Generate historical data
    print("\n1. Generating historical data...")
    historical_data = system.generate_simulated_historical_data(days=30)
    assert len(historical_data) > 0
    print(f"✓ Generated {len(historical_data)} data points")
    
    # Train model
    print("\n2. Training AI model...")
    model = system.train_prediction_model(historical_data)
    assert model is not None
    print("✓ Model trained successfully")
    
    # Make prediction
    print("\n3. Making prediction...")
    prediction = system.predict_availability("Lot K", hours_ahead=2)
    assert prediction is not None
    assert prediction >= 0
    print(f"✓ Prediction made: {prediction} spots")
    
    print("\n✅ All AI prediction tests PASSED\n")


def test_auto_checkout():
    """Test auto-checkout for forgotten users"""
    print("\n" + "="*70)
    print("TEST 4: AUTO-CHECKOUT FUNCTIONALITY")
    print("="*70)
    
    system = ParkingSystem()
    
    # Simulate old check-in
    print("\n1. Simulating user who forgot to check out...")
    lot_k = system.lots["Lot K"]
    
    # Manually add old check-in
    from datetime import datetime, timedelta
    old_time = datetime.now() - timedelta(hours=5)
    lot_k.checked_in_users["forgotten_user"] = old_time
    lot_k.current_occupancy += 1
    
    initial_occupancy = lot_k.current_occupancy
    print(f"Initial occupancy: {initial_occupancy}")
    
    # Run auto-checkout
    print("\n2. Running auto-checkout (3 hour threshold)...")
    system.auto_checkout_forgotten_users("Lot K", hours_threshold=3)
    
    final_occupancy = lot_k.current_occupancy
    print(f"Final occupancy: {final_occupancy}")
    assert final_occupancy == initial_occupancy - 1
    print("✓ Forgotten user automatically checked out")
    
    print("\n✅ All auto-checkout tests PASSED\n")


def test_multiple_lots():
    """Test operations across multiple parking lots"""
    print("\n" + "="*70)
    print("TEST 5: MULTIPLE PARKING LOTS")
    print("="*70)
    
    system = ParkingSystem()
    
    print("\n1. Verifying all lots loaded...")
    assert len(system.lots) == 14
    print(f"✓ All 14 parking lots loaded")
    
    print("\n2. Testing operations across different lots...")
    system.check_in("user_1", "Lot K")
    system.check_in("user_2", "Lot A")
    system.check_in("user_3", "West Campus Lot")
    
    # Verify each lot has correct occupancy
    assert system.lots["Lot K"].current_occupancy == 1
    assert system.lots["Lot A"].current_occupancy == 1
    assert system.lots["West Campus Lot"].current_occupancy == 1
    print("✓ Users checked in to different lots independently")
    
    print("\n3. Getting best available lots...")
    system.get_best_lots(top_n=3)
    print("✓ Best lots retrieved successfully")
    
    print("\n✅ All multiple lot tests PASSED\n")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*70)
    print("SMART PARKING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    start_time = time.time()
    
    try:
        test_basic_functionality()
        test_availability_tracking()
        test_ai_prediction()
        test_auto_checkout()
        test_multiple_lots()
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("="*70)
        print(f"Total time: {elapsed_time:.2f} seconds")
        print("\nYour Smart Parking System is working correctly! ✅")
        print("\nNext steps:")
        print("1. Run 'python api_server.py' to start the API")
        print("2. Open 'index.html' in a web browser to see the UI")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\nPlease check the code and try again.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nAn unexpected error occurred.")


if __name__ == "__main__":
    run_all_tests()
