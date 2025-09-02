#!/usr/bin/env python3
"""
Command-line interface for disaster predictions
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def get_float_input(prompt, default=None):
    """Get float input with default value"""
    while True:
        try:
            value = input(f"{prompt} [{default}]: ").strip()
            if not value and default is not None:
                return float(default)
            return float(value)
        except ValueError:
            print("Please enter a valid number.")

def get_choice_input(prompt, choices, default=None):
    """Get choice input from list"""
    print(f"{prompt}")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}")
    
    while True:
        try:
            value = input(f"Choose (1-{len(choices)}) [{default}]: ").strip()
            if not value and default is not None:
                return choices[int(default) - 1]
            choice_idx = int(value) - 1
            if 0 <= choice_idx < len(choices):
                return choices[choice_idx]
            else:
                print(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print("Please enter a valid number.")

def predict_flood():
    """Interactive flood prediction"""
    print("\n🌊 FLOOD PREDICTION")
    print("=" * 40)
    
    # Get inputs
    latitude = get_float_input("Latitude", 37.7749)
    longitude = get_float_input("Longitude", -122.4194)
    temperature = get_float_input("Temperature (°C)", 20)
    humidity = get_float_input("Humidity (%)", 60)
    precipitation_24h = get_float_input("Precipitation last 24h (mm)", 0)
    precipitation_48h = get_float_input("Precipitation last 48h (mm)", 0)
    wind_speed = get_float_input("Wind speed (m/s)", 5)
    water_level = get_float_input("Water level (m)", 2)
    river_flow = get_float_input("River flow rate (m³/s)", 100)
    elevation = get_float_input("Elevation (m)", 100)
    
    soil_types = ["clay", "sand", "loam", "rock"]
    soil_type = get_choice_input("Soil type:", soil_types, 3)
    
    # Prepare data
    data = {
        "latitude": latitude,
        "longitude": longitude,
        "temperature": temperature,
        "humidity": humidity,
        "precipitation_24h": precipitation_24h,
        "precipitation_48h": precipitation_48h,
        "wind_speed": wind_speed,
        "water_level": water_level,
        "river_flow": river_flow,
        "elevation": elevation,
        "soil_type": soil_type
    }
    
    # Make prediction
    try:
        response = requests.post(f"{BASE_URL}/api/v1/predict/flood", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("\n📊 FLOOD PREDICTION RESULT")
            print("=" * 40)
            print(f"📍 Location: {result['latitude']:.4f}, {result['longitude']:.4f}")
            print(f"🌊 Flood Probability: {result['flood_probability']:.1%}")
            print(f"⚠️  Risk Level: {result['risk_level']}")
            print(f"🎯 Confidence: {result['confidence_score']:.1%}")
            print(f"🕒 Prediction Time: {result['prediction_time']}")
            
            if result.get('factors'):
                print("\n📋 Key Risk Factors:")
                for factor in result['factors']:
                    print(f"   • {factor}")
            
            # Risk interpretation
            print(f"\n💡 Risk Interpretation:")
            if result['flood_probability'] < 0.3:
                print("   🟢 LOW RISK: Flooding is unlikely under current conditions.")
            elif result['flood_probability'] < 0.6:
                print("   🟡 MEDIUM RISK: Some flood risk exists. Monitor conditions.")
            elif result['flood_probability'] < 0.8:
                print("   🟠 HIGH RISK: Significant flood risk. Take precautions.")
            else:
                print("   🔴 CRITICAL RISK: Very high flood risk. Evacuate if necessary.")
                
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def predict_earthquake():
    """Interactive earthquake prediction"""
    print("\n🏔️ EARTHQUAKE PREDICTION")
    print("=" * 40)
    
    # Get inputs
    latitude = get_float_input("Latitude", 37.7749)
    longitude = get_float_input("Longitude", -122.4194)
    recent_earthquakes = get_float_input("Recent earthquakes (30 days)", 2)
    max_magnitude_30d = get_float_input("Max magnitude last 30 days", 3.5)
    avg_magnitude = get_float_input("Average magnitude", 3.0)
    depth_avg = get_float_input("Average depth (km)", 10)
    fault_distance = get_float_input("Distance to nearest fault (km)", 50)
    population_density = get_float_input("Population density (per km²)", 100)
    
    tectonic_levels = ["low", "medium", "high"]
    tectonic_activity = get_choice_input("Tectonic activity level:", tectonic_levels, 1)
    
    stability_levels = ["stable", "moderate", "unstable"]
    geological_stability = get_choice_input("Geological stability:", stability_levels, 1)
    
    # Prepare data
    data = {
        "latitude": latitude,
        "longitude": longitude,
        "recent_earthquakes": int(recent_earthquakes),
        "max_magnitude_30d": max_magnitude_30d,
        "avg_magnitude": avg_magnitude,
        "depth_avg": depth_avg,
        "fault_distance": fault_distance,
        "tectonic_activity": tectonic_activity,
        "geological_stability": geological_stability,
        "population_density": population_density
    }
    
    # Make prediction
    try:
        response = requests.post(f"{BASE_URL}/api/v1/predict/earthquake", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("\n📊 EARTHQUAKE PREDICTION RESULT")
            print("=" * 40)
            print(f"📍 Location: {result['latitude']:.4f}, {result['longitude']:.4f}")
            print(f"🏔️ Risk Probability: {result['risk_probability']:.1%}")
            print(f"📏 Estimated Magnitude: M{result['estimated_magnitude']}")
            print(f"⚠️  Risk Level: {result['risk_level']}")
            print(f"🎯 Confidence: {result['confidence_score']:.1%}")
            print(f"🕒 Prediction Time: {result['prediction_time']}")
            
            if result.get('factors'):
                print("\n📋 Key Risk Factors:")
                for factor in result['factors']:
                    print(f"   • {factor}")
            
            # Risk interpretation
            print(f"\n💡 Risk Interpretation:")
            if result['risk_probability'] < 0.3:
                print("   🟢 LOW RISK: Earthquake activity is minimal.")
            elif result['risk_probability'] < 0.6:
                print("   🟡 MEDIUM RISK: Moderate earthquake risk. Stay prepared.")
            elif result['risk_probability'] < 0.8:
                print("   🟠 HIGH RISK: Elevated earthquake risk. Review safety plans.")
            else:
                print("   🔴 CRITICAL RISK: Very high earthquake risk. Take immediate precautions.")
                
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def main():
    """Main CLI function"""
    print("🌍 DISASTER MANAGEMENT PREDICTION CLI")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server not responding. Make sure the application is running on http://localhost:8000")
            sys.exit(1)
    except Exception:
        print("❌ Cannot connect to server. Make sure the application is running on http://localhost:8000")
        print("   Run: python app.py")
        sys.exit(1)
    
    while True:
        print("\nChoose prediction type:")
        print("1. 🌊 Flood Prediction")
        print("2. 🏔️ Earthquake Prediction")
        print("3. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            predict_flood()
        elif choice == "2":
            predict_earthquake()
        elif choice == "3":
            print("\n👋 Thank you for using the Disaster Management Prediction System!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
