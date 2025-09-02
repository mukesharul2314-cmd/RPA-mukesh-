#!/usr/bin/env python3
"""
Test script to demonstrate prediction functionality
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_flood_prediction():
    """Test flood prediction with sample data"""
    print("🌊 Testing Flood Prediction...")
    
    # Sample flood prediction data
    flood_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "temperature": 25,
        "humidity": 85,
        "precipitation_24h": 75,  # Heavy rain
        "precipitation_48h": 120,  # Very heavy rain over 48h
        "wind_speed": 15,
        "water_level": 4.5,  # High water level
        "river_flow": 350,
        "elevation": 45,  # Low elevation
        "soil_type": "clay"  # Poor drainage
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/predict/flood", json=flood_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Flood Prediction Successful!")
            print(f"   📍 Location: {result['latitude']}, {result['longitude']}")
            print(f"   🌊 Flood Probability: {result['flood_probability']:.1%}")
            print(f"   ⚠️  Risk Level: {result['risk_level']}")
            print(f"   🎯 Confidence: {result['confidence_score']:.1%}")
            
            if result.get('factors'):
                print("   📋 Key Risk Factors:")
                for factor in result['factors']:
                    print(f"      • {factor}")
            
            print()
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_earthquake_prediction():
    """Test earthquake prediction with sample data"""
    print("🏔️ Testing Earthquake Prediction...")
    
    # Sample earthquake prediction data
    earthquake_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "recent_earthquakes": 8,  # High recent activity
        "max_magnitude_30d": 5.2,  # Significant recent earthquake
        "avg_magnitude": 3.8,
        "depth_avg": 8,  # Shallow earthquakes
        "fault_distance": 15,  # Close to fault line
        "tectonic_activity": "high",
        "geological_stability": "moderate",
        "population_density": 1500
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/predict/earthquake", json=earthquake_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Earthquake Prediction Successful!")
            print(f"   📍 Location: {result['latitude']}, {result['longitude']}")
            print(f"   🏔️ Risk Probability: {result['risk_probability']:.1%}")
            print(f"   📏 Estimated Magnitude: M{result['estimated_magnitude']}")
            print(f"   ⚠️  Risk Level: {result['risk_level']}")
            print(f"   🎯 Confidence: {result['confidence_score']:.1%}")
            
            if result.get('factors'):
                print("   📋 Key Risk Factors:")
                for factor in result['factors']:
                    print(f"      • {factor}")
            
            print()
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_low_risk_scenarios():
    """Test low risk scenarios"""
    print("🟢 Testing Low Risk Scenarios...")
    
    # Low risk flood scenario
    low_flood_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "temperature": 22,
        "humidity": 45,
        "precipitation_24h": 2,  # Light rain
        "precipitation_48h": 5,
        "wind_speed": 8,
        "water_level": 1.5,  # Normal water level
        "river_flow": 80,
        "elevation": 200,  # High elevation
        "soil_type": "sand"  # Good drainage
    }
    
    # Low risk earthquake scenario
    low_earthquake_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "recent_earthquakes": 1,  # Low activity
        "max_magnitude_30d": 2.8,  # Small earthquakes
        "avg_magnitude": 2.2,
        "depth_avg": 25,  # Deep earthquakes
        "fault_distance": 150,  # Far from fault lines
        "tectonic_activity": "low",
        "geological_stability": "stable",
        "population_density": 800
    }
    
    # Test low risk flood
    response = requests.post(f"{BASE_URL}/api/v1/predict/flood", json=low_flood_data)
    if response.status_code == 200:
        result = response.json()
        print(f"   🌊 Low Risk Flood: {result['risk_level']} ({result['flood_probability']:.1%})")
    
    # Test low risk earthquake
    response = requests.post(f"{BASE_URL}/api/v1/predict/earthquake", json=low_earthquake_data)
    if response.status_code == 200:
        result = response.json()
        print(f"   🏔️ Low Risk Earthquake: {result['risk_level']} ({result['risk_probability']:.1%})")
    
    print()

def test_api_endpoints():
    """Test basic API endpoints"""
    print("🔍 Testing API Endpoints...")
    
    endpoints = [
        ("/health", "Health Check"),
        ("/api/v1/status", "System Status"),
        ("/docs", "API Documentation")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 200:
                print(f"   ✅ {name}: OK")
            else:
                print(f"   ❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: Connection Error")
    
    print()

def main():
    """Main test function"""
    print("🧪 Disaster Management Prediction Tests")
    print("=" * 50)
    
    # Test basic endpoints
    test_api_endpoints()
    
    # Test predictions
    flood_success = test_flood_prediction()
    earthquake_success = test_earthquake_prediction()
    
    # Test low risk scenarios
    test_low_risk_scenarios()
    
    # Summary
    print("📊 Test Summary:")
    print(f"   🌊 Flood Prediction: {'✅ PASS' if flood_success else '❌ FAIL'}")
    print(f"   🏔️ Earthquake Prediction: {'✅ PASS' if earthquake_success else '❌ FAIL'}")
    
    if flood_success and earthquake_success:
        print("\n🎉 All tests passed! The prediction system is working correctly.")
        print("\n💡 Try different input values to see how predictions change:")
        print("   • Increase precipitation for higher flood risk")
        print("   • Increase recent earthquakes for higher seismic risk")
        print("   • Change elevation and soil type for flood predictions")
        print("   • Adjust fault distance for earthquake predictions")
    else:
        print("\n⚠️ Some tests failed. Check if the server is running on http://localhost:8000")

if __name__ == "__main__":
    main()
