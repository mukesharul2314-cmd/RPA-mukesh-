# 🌍 Disaster Management Prediction System - User Guide

## 🚀 Quick Start

The system is now running with full prediction capabilities! You can input your own values and get real disaster risk predictions.

### 🌐 Access Methods

1. **Web Dashboard**: http://localhost:8000/dashboard/
2. **API Documentation**: http://localhost:8000/docs
3. **Command Line Interface**: `python predict_cli.py`
4. **Direct API Calls**: Use the REST endpoints

---

## 🌊 Flood Prediction

### Input Parameters

| Parameter | Description | Example Values | Impact |
|-----------|-------------|----------------|---------|
| **Latitude/Longitude** | Location coordinates | 37.7749, -122.4194 | Location-specific factors |
| **Temperature (°C)** | Current temperature | 15-35°C | Affects evaporation |
| **Humidity (%)** | Air humidity | 30-95% | Higher = more moisture |
| **Precipitation 24h (mm)** | Rain in last 24 hours | 0-200mm | **Major factor** |
| **Precipitation 48h (mm)** | Rain in last 48 hours | 0-300mm | **Major factor** |
| **Wind Speed (m/s)** | Current wind speed | 0-30 m/s | Can worsen flooding |
| **Water Level (m)** | Current water level | 0-10m | **Critical factor** |
| **River Flow (m³/s)** | River flow rate | 50-1000 m³/s | Higher = more risk |
| **Elevation (m)** | Ground elevation | 0-500m | Lower = higher risk |
| **Soil Type** | Drainage capability | clay/sand/loam/rock | Clay = poor drainage |

### 🎯 Risk Levels

- **🟢 LOW (0-30%)**: Flooding unlikely
- **🟡 MEDIUM (30-60%)**: Some risk, monitor conditions
- **🟠 HIGH (60-80%)**: Significant risk, take precautions
- **🔴 CRITICAL (80%+)**: Very high risk, consider evacuation

### 📊 Example Scenarios

**High Risk Scenario:**
```json
{
  "precipitation_24h": 75,
  "precipitation_48h": 120,
  "water_level": 4.5,
  "elevation": 45,
  "soil_type": "clay"
}
```
*Result: CRITICAL risk (95% probability)*

**Low Risk Scenario:**
```json
{
  "precipitation_24h": 2,
  "precipitation_48h": 5,
  "water_level": 1.5,
  "elevation": 200,
  "soil_type": "sand"
}
```
*Result: LOW risk (5% probability)*

---

## 🏔️ Earthquake Prediction

### Input Parameters

| Parameter | Description | Example Values | Impact |
|-----------|-------------|----------------|---------|
| **Latitude/Longitude** | Location coordinates | 37.7749, -122.4194 | Seismic zone factors |
| **Recent Earthquakes** | Count in last 30 days | 0-20 | **Major factor** |
| **Max Magnitude 30d** | Largest recent earthquake | 2.0-8.0 | **Critical factor** |
| **Average Magnitude** | Average of recent quakes | 2.0-6.0 | Baseline activity |
| **Average Depth (km)** | Earthquake depth | 5-50 km | Shallow = more dangerous |
| **Fault Distance (km)** | Distance to nearest fault | 0-500 km | **Major factor** |
| **Tectonic Activity** | Regional activity level | low/medium/high | Geological setting |
| **Geological Stability** | Ground stability | stable/moderate/unstable | Foundation strength |
| **Population Density** | People per km² | 10-5000 | Impact assessment |

### 🎯 Risk Levels

- **🟢 LOW (0-30%)**: Minimal earthquake activity
- **🟡 MEDIUM (30-60%)**: Moderate risk, stay prepared
- **🟠 HIGH (60-80%)**: Elevated risk, review safety plans
- **🔴 CRITICAL (80%+)**: Very high risk, immediate precautions

### 📊 Example Scenarios

**High Risk Scenario:**
```json
{
  "recent_earthquakes": 8,
  "max_magnitude_30d": 5.2,
  "fault_distance": 15,
  "tectonic_activity": "high",
  "geological_stability": "moderate"
}
```
*Result: CRITICAL risk (90% probability, M4.9 estimated)*

**Low Risk Scenario:**
```json
{
  "recent_earthquakes": 1,
  "max_magnitude_30d": 2.8,
  "fault_distance": 150,
  "tectonic_activity": "low",
  "geological_stability": "stable"
}
```
*Result: LOW risk (10% probability, M3.2 estimated)*

---

## 🖥️ How to Use

### 1. Web Dashboard
1. Open http://localhost:8000/dashboard/
2. Scroll down to "Prediction Tools"
3. Fill in the form fields
4. Click "Predict Flood Risk" or "Predict Earthquake Risk"
5. View results with risk factors

### 2. Command Line Interface
```bash
python predict_cli.py
```
- Interactive prompts for all parameters
- Default values provided
- Detailed result interpretation

### 3. API Calls (Python)
```python
import requests

# Flood prediction
flood_data = {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "precipitation_24h": 50,
    "water_level": 3.5,
    # ... other parameters
}

response = requests.post(
    "http://localhost:8000/api/v1/predict/flood", 
    json=flood_data
)
result = response.json()
print(f"Flood Risk: {result['risk_level']}")
```

### 4. API Calls (curl)
```bash
curl -X POST "http://localhost:8000/api/v1/predict/flood" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 37.7749,
    "longitude": -122.4194,
    "precipitation_24h": 50,
    "water_level": 3.5,
    "elevation": 100,
    "soil_type": "clay"
  }'
```

---

## 🧪 Testing

Run the automated test suite:
```bash
python test_predictions.py
```

This will test:
- ✅ API endpoints
- ✅ High-risk flood scenario
- ✅ High-risk earthquake scenario
- ✅ Low-risk scenarios
- ✅ Error handling

---

## 🔬 How the Predictions Work

### Flood Prediction Algorithm
1. **Precipitation Analysis**: Heavy rain increases risk exponentially
2. **Water Level Assessment**: Current water levels vs. normal
3. **Drainage Evaluation**: Soil type and elevation factors
4. **Environmental Conditions**: Temperature, humidity, wind effects
5. **Risk Calculation**: Weighted combination of all factors

### Earthquake Prediction Algorithm
1. **Seismic Activity Analysis**: Recent earthquake patterns
2. **Geological Assessment**: Fault proximity and stability
3. **Historical Context**: Past earthquake magnitudes
4. **Tectonic Evaluation**: Regional activity levels
5. **Risk Calculation**: Probability and magnitude estimation

### Confidence Scoring
- Based on data completeness and quality
- Higher confidence with more complete input data
- Critical parameters weighted more heavily

---

## 🎯 Tips for Accurate Predictions

### For Flood Predictions:
- **Most Important**: Precipitation data and water levels
- Use recent weather data (last 24-48 hours)
- Consider local drainage and elevation
- Clay soil = higher risk, sandy soil = lower risk

### For Earthquake Predictions:
- **Most Important**: Recent seismic activity and fault distance
- Include all earthquakes in the last 30 days
- Shallow earthquakes (< 10km) are more dangerous
- Proximity to fault lines significantly increases risk

### General Tips:
- Provide accurate coordinates for location-specific factors
- Use real-time data when available
- Consider multiple scenarios (best/worst case)
- Update predictions as conditions change

---

## 🚨 Important Notes

⚠️ **This is a demonstration system** - For real disaster management:
- Use official meteorological and seismological data
- Consult with local emergency services
- Follow official evacuation and safety protocols
- This system is for educational and planning purposes

🔄 **Real-time Updates**: In production, this system would:
- Automatically collect data from weather stations
- Monitor seismic networks continuously
- Send automated alerts for high-risk conditions
- Integrate with emergency response systems

---

## 📞 Support

If you encounter issues:
1. Check that the server is running: http://localhost:8000/health
2. Verify all required parameters are provided
3. Check the API documentation: http://localhost:8000/docs
4. Review the console output for error messages

**Happy Predicting! 🌍**
