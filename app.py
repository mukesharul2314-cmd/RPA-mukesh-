#!/usr/bin/env python3
"""
Simple FastAPI application for disaster management
"""
import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

import os
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException
    print("✅ FastAPI imported successfully")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")
    print("Installing FastAPI....") 
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    from fastapi import FastAPI, HTTPException
try:
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    print("✅ All FastAPI modules imported successfully")
except ImportError as e:
    print(f"❌ FastAPI modules import failed: {e}")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Disaster Management Predictive Analytics API",
    description="API for flood and earthquake prediction and monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="src/dashboard/static"), name="static")
except:
    pass  # Static files not found, continue without them

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Disaster Management Predictive Analytics API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow(),
        "mode": "simplified"
    }

@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors"""
    return {"message": "No favicon"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "sqlite",
        "timestamp": datetime.utcnow()
    }

@app.get("/api/v1/status")
async def system_status():
    """Get system status and statistics"""
    return {
        "system_status": "operational",
        "data_counts": {
            "weather_records": 0,
            "seismic_records": 0,
            "flood_predictions": 0,
            "earthquake_predictions": 0,
            "active_alerts": 0
        },
        "recent_activity": {
            "weather_records_24h": 0,
            "seismic_records_24h": 0
        },
        "timestamp": datetime.utcnow(),
        "mode": "simplified"
    }

@app.get("/dashboard/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Disaster Management Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body { background-color: #f8f9fa; }
            .card { border: none; box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075); }
            .status-card { text-align: center; padding: 2rem; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">
                    <i class="fas fa-shield-alt"></i> Disaster Management
                </a>
                <span class="navbar-text">
                    <span class="badge bg-success">
                        <i class="fas fa-circle"></i> Operational
                    </span>
                </span>
            </div>
        </nav>

        <div class="container-fluid mt-4">
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body status-card">
                            <h1 class="text-success">
                                <i class="fas fa-check-circle"></i>
                                System Running Successfully!
                            </h1>
                            <p class="lead">Disaster Management Predictive Analytics System is operational.</p>
                            
                            <div class="row mt-4">
                                <div class="col-md-4">
                                    <div class="card bg-primary text-white">
                                        <div class="card-body">
                                            <h5><i class="fas fa-server"></i> API Status</h5>
                                            <p>Operational</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card bg-info text-white">
                                        <div class="card-body">
                                            <h5><i class="fas fa-database"></i> Database</h5>
                                            <p>SQLite Ready</p>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card bg-success text-white">
                                        <div class="card-body">
                                            <h5><i class="fas fa-chart-line"></i> Analytics</h5>
                                            <p>Ready</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="mt-4">
                                <h3>Available Endpoints</h3>
                                <div class="list-group">
                                    <a href="/docs" class="list-group-item list-group-item-action" target="_blank">
                                        <i class="fas fa-book"></i> API Documentation
                                    </a>
                                    <a href="/health" class="list-group-item list-group-item-action" target="_blank">
                                        <i class="fas fa-heartbeat"></i> Health Check
                                    </a>
                                    <a href="/api/v1/status" class="list-group-item list-group-item-action" target="_blank">
                                        <i class="fas fa-info-circle"></i> System Status
                                    </a>
                                    <a href="javascript:void(0)" class="list-group-item list-group-item-action" onclick="testConnection()">
                                        <i class="fas fa-wifi"></i> Test Connection
                                    </a>
                                </div>
                            </div>

                            <div class="mt-4">
                                <h3>Prediction Tools</h3>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="card">
                                            <div class="card-header">
                                                <h5><i class="fas fa-water text-primary"></i> Flood Prediction</h5>
                                            </div>
                                            <div class="card-body">
                                                <form id="floodForm">
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Latitude</label>
                                                                <input type="number" class="form-control form-control-sm" name="latitude" step="0.000001" value="37.7749" required>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Longitude</label>
                                                                <input type="number" class="form-control form-control-sm" name="longitude" step="0.000001" value="-122.4194" required>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Temperature (°C)</label>
                                                                <input type="number" class="form-control form-control-sm" name="temperature" value="20" required>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Humidity (%)</label>
                                                                <input type="number" class="form-control form-control-sm" name="humidity" value="60" required>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Precipitation 24h (mm)</label>
                                                                <input type="number" class="form-control form-control-sm" name="precipitation_24h" value="0" required>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Water Level (m)</label>
                                                                <input type="number" class="form-control form-control-sm" name="water_level" value="2" required>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Elevation (m)</label>
                                                                <input type="number" class="form-control form-control-sm" name="elevation" value="100" required>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Soil Type</label>
                                                                <select class="form-select form-select-sm" name="soil_type" required>
                                                                    <option value="clay">Clay</option>
                                                                    <option value="sand">Sand</option>
                                                                    <option value="loam" selected>Loam</option>
                                                                    <option value="rock">Rock</option>
                                                                </select>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <button type="submit" class="btn btn-primary btn-sm w-100">
                                                        <i class="fas fa-chart-line"></i> Predict Flood Risk
                                                    </button>
                                                </form>
                                                <div id="floodResult" class="mt-3" style="display: none;"></div>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="col-md-6">
                                        <div class="card">
                                            <div class="card-header">
                                                <h5><i class="fas fa-mountain text-warning"></i> Earthquake Prediction</h5>
                                            </div>
                                            <div class="card-body">
                                                <form id="earthquakeForm">
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Latitude</label>
                                                                <input type="number" class="form-control form-control-sm" name="latitude" step="0.000001" value="37.7749" required>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Longitude</label>
                                                                <input type="number" class="form-control form-control-sm" name="longitude" step="0.000001" value="-122.4194" required>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Recent Earthquakes (30d)</label>
                                                                <input type="number" class="form-control form-control-sm" name="recent_earthquakes" value="2" required>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Max Magnitude (30d)</label>
                                                                <input type="number" class="form-control form-control-sm" name="max_magnitude_30d" step="0.1" value="3.5" required>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Fault Distance (km)</label>
                                                                <input type="number" class="form-control form-control-sm" name="fault_distance" value="50" required>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Avg Depth (km)</label>
                                                                <input type="number" class="form-control form-control-sm" name="depth_avg" value="10" required>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="row">
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Tectonic Activity</label>
                                                                <select class="form-select form-select-sm" name="tectonic_activity" required>
                                                                    <option value="low" selected>Low</option>
                                                                    <option value="medium">Medium</option>
                                                                    <option value="high">High</option>
                                                                </select>
                                                            </div>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <div class="mb-2">
                                                                <label class="form-label">Geological Stability</label>
                                                                <select class="form-select form-select-sm" name="geological_stability" required>
                                                                    <option value="stable" selected>Stable</option>
                                                                    <option value="moderate">Moderate</option>
                                                                    <option value="unstable">Unstable</option>
                                                                </select>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <button type="submit" class="btn btn-warning btn-sm w-100">
                                                        <i class="fas fa-chart-line"></i> Predict Earthquake Risk
                                                    </button>
                                                </form>
                                                <div id="earthquakeResult" class="mt-3" style="display: none;"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Flood prediction form handler
            document.getElementById('floodForm').addEventListener('submit', async function(e) {
                e.preventDefault();

                const formData = new FormData(this);
                const data = {};
                for (let [key, value] of formData.entries()) {
                    data[key] = value;
                }

                const resultDiv = document.getElementById('floodResult');
                resultDiv.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Calculating...</div>';
                resultDiv.style.display = 'block';

                try {
                    const response = await fetch('/api/v1/predict/flood', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data),
                        timeout: 10000
                    });

                    const result = await response.json();

                    if (response.ok) {
                        const riskColor = getRiskColor(result.risk_level);
                        resultDiv.innerHTML = `
                            <div class="alert alert-${riskColor}">
                                <h6><i class="fas fa-water"></i> Flood Prediction Result</h6>
                                <p><strong>Risk Level:</strong> <span class="badge bg-${riskColor}">${result.risk_level}</span></p>
                                <p><strong>Probability:</strong> ${(result.flood_probability * 100).toFixed(1)}%</p>
                                <p><strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(1)}%</p>
                                <p><strong>Location:</strong> ${result.latitude.toFixed(4)}, ${result.longitude.toFixed(4)}</p>
                                ${result.factors && result.factors.length > 0 ?
                                    '<p><strong>Key Factors:</strong><br>' + result.factors.map(f => '• ' + f).join('<br>') + '</p>'
                                    : ''}
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${result.detail}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
                }
            });

            // Earthquake prediction form handler
            document.getElementById('earthquakeForm').addEventListener('submit', async function(e) {
                e.preventDefault();

                const formData = new FormData(this);
                const data = {};
                for (let [key, value] of formData.entries()) {
                    data[key] = value;
                }

                const resultDiv = document.getElementById('earthquakeResult');
                resultDiv.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Calculating...</div>';
                resultDiv.style.display = 'block';

                try {
                    const response = await fetch('/api/v1/predict/earthquake', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data),
                        timeout: 10000
                    });

                    const result = await response.json();

                    if (response.ok) {
                        const riskColor = getRiskColor(result.risk_level);
                        resultDiv.innerHTML = `
                            <div class="alert alert-${riskColor}">
                                <h6><i class="fas fa-mountain"></i> Earthquake Prediction Result</h6>
                                <p><strong>Risk Level:</strong> <span class="badge bg-${riskColor}">${result.risk_level}</span></p>
                                <p><strong>Risk Probability:</strong> ${(result.risk_probability * 100).toFixed(1)}%</p>
                                <p><strong>Estimated Magnitude:</strong> M${result.estimated_magnitude}</p>
                                <p><strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(1)}%</p>
                                <p><strong>Location:</strong> ${result.latitude.toFixed(4)}, ${result.longitude.toFixed(4)}</p>
                                ${result.factors && result.factors.length > 0 ?
                                    '<p><strong>Key Factors:</strong><br>' + result.factors.map(f => '• ' + f).join('<br>') + '</p>'
                                    : ''}
                            </div>
                        `;
                    } else {
                        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${result.detail}</div>`;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
                }
            });

            function getRiskColor(riskLevel) {
                switch(riskLevel) {
                    case 'LOW': return 'success';
                    case 'MEDIUM': return 'warning';
                    case 'HIGH': return 'danger';
                    case 'CRITICAL': return 'danger';
                    default: return 'secondary';
                }
            }

            function testConnection() {
                fetch('/health')
                    .then(response => response.json())
                    .then(data => {
                        alert('✅ Connection successful! Server is running.');
                    })
                    .catch(error => {
                        alert('❌ Connection failed: ' + error.message);
                    });
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/test", response_class=HTMLResponse)
async def simple_test():
    """Serve simple test page"""
    try:
        with open("simple_test.html", 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading test page</h1><p>{str(e)}</p>")


@app.post("/api/v1/predict/flood")
async def predict_flood(prediction_data: dict):
    """Flood prediction with user inputs"""
    try:
        # Extract input parameters
        latitude = float(prediction_data.get('latitude', 0))
        longitude = float(prediction_data.get('longitude', 0))
        temperature = float(prediction_data.get('temperature', 20))
        humidity = float(prediction_data.get('humidity', 60))
        precipitation_24h = float(prediction_data.get('precipitation_24h', 0))
        precipitation_48h = float(prediction_data.get('precipitation_48h', 0))
        wind_speed = float(prediction_data.get('wind_speed', 5))
        water_level = float(prediction_data.get('water_level', 2))
        river_flow = float(prediction_data.get('river_flow', 100))
        elevation = float(prediction_data.get('elevation', 100))
        soil_type = prediction_data.get('soil_type', 'clay')

        # Calculate flood probability based on inputs
        probability = calculate_flood_probability(
            temperature, humidity, precipitation_24h, precipitation_48h,
            wind_speed, water_level, river_flow, elevation, soil_type
        )

        # Determine risk level
        if probability < 0.3:
            risk_level = "LOW"
        elif probability < 0.6:
            risk_level = "MEDIUM"
        elif probability < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Calculate confidence based on data quality
        confidence = calculate_confidence(prediction_data)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "flood_probability": round(probability, 3),
            "risk_level": risk_level,
            "confidence_score": round(confidence, 3),
            "prediction_time": datetime.utcnow(),
            "model_version": "v1.0",
            "input_parameters": prediction_data,
            "factors": analyze_flood_factors(prediction_data)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in flood prediction: {str(e)}")

@app.get("/api/v1/demo/predict/flood")
async def demo_flood_prediction(latitude: float = 37.7749, longitude: float = -122.4194):
    """Demo flood prediction endpoint (for backward compatibility)"""
    import random

    probability = random.uniform(0.1, 0.9)

    if probability < 0.3:
        risk_level = "LOW"
    elif probability < 0.6:
        risk_level = "MEDIUM"
    elif probability < 0.8:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    return {
        "latitude": latitude,
        "longitude": longitude,
        "flood_probability": round(probability, 2),
        "risk_level": risk_level,
        "confidence_score": round(random.uniform(0.6, 0.9), 2),
        "prediction_time": datetime.utcnow(),
        "model_version": "demo",
        "note": "This is a demo prediction with random values"
    }

@app.post("/api/v1/predict/earthquake")
async def predict_earthquake(prediction_data: dict):
    """Earthquake prediction with user inputs"""
    try:
        # Extract input parameters
        latitude = float(prediction_data.get('latitude', 0))
        longitude = float(prediction_data.get('longitude', 0))
        recent_earthquakes = int(prediction_data.get('recent_earthquakes', 0))
        max_magnitude_30d = float(prediction_data.get('max_magnitude_30d', 0))
        avg_magnitude = float(prediction_data.get('avg_magnitude', 0))
        depth_avg = float(prediction_data.get('depth_avg', 10))
        fault_distance = float(prediction_data.get('fault_distance', 50))
        tectonic_activity = prediction_data.get('tectonic_activity', 'low')
        geological_stability = prediction_data.get('geological_stability', 'stable')
        population_density = float(prediction_data.get('population_density', 100))

        # Calculate earthquake probability based on inputs
        probability = calculate_earthquake_probability(
            recent_earthquakes, max_magnitude_30d, avg_magnitude, depth_avg,
            fault_distance, tectonic_activity, geological_stability
        )

        # Estimate magnitude
        estimated_magnitude = estimate_earthquake_magnitude(
            max_magnitude_30d, avg_magnitude, recent_earthquakes, fault_distance
        )

        # Determine risk level
        if probability < 0.3:
            risk_level = "LOW"
        elif probability < 0.6:
            risk_level = "MEDIUM"
        elif probability < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        # Calculate confidence
        confidence = calculate_confidence(prediction_data)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "risk_probability": round(probability, 3),
            "estimated_magnitude": round(estimated_magnitude, 1),
            "risk_level": risk_level,
            "confidence_score": round(confidence, 3),
            "prediction_time": datetime.utcnow(),
            "model_version": "v1.0",
            "input_parameters": prediction_data,
            "factors": analyze_earthquake_factors(prediction_data)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in earthquake prediction: {str(e)}")

@app.get("/api/v1/demo/predict/earthquake")
async def demo_earthquake_prediction(latitude: float = 37.7749, longitude: float = -122.4194):
    """Demo earthquake prediction endpoint (for backward compatibility)"""
    import random

    probability = random.uniform(0.1, 0.8)
    magnitude = random.uniform(3.0, 7.0)

    if probability < 0.3:
        risk_level = "LOW"
    elif probability < 0.6:
        risk_level = "MEDIUM"
    elif probability < 0.8:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    return {
        "latitude": latitude,
        "longitude": longitude,
        "risk_probability": round(probability, 2),
        "estimated_magnitude": round(magnitude, 1),
        "risk_level": risk_level,
        "confidence_score": round(random.uniform(0.6, 0.9), 2),
        "prediction_time": datetime.utcnow(),
        "model_version": "demo",
        "note": "This is a demo prediction with random values"
    }

# Prediction calculation functions
def calculate_flood_probability(temperature, humidity, precipitation_24h, precipitation_48h,
                               wind_speed, water_level, river_flow, elevation, soil_type):
    """Calculate flood probability based on input parameters"""
    import math

    # Base probability
    probability = 0.1

    # Precipitation factor (most important)
    if precipitation_24h > 50:
        probability += 0.4
    elif precipitation_24h > 25:
        probability += 0.2
    elif precipitation_24h > 10:
        probability += 0.1

    if precipitation_48h > 100:
        probability += 0.3
    elif precipitation_48h > 50:
        probability += 0.15

    # Water level factor
    if water_level > 5:
        probability += 0.3
    elif water_level > 3:
        probability += 0.15

    # River flow factor
    if river_flow > 500:
        probability += 0.2
    elif river_flow > 200:
        probability += 0.1

    # Elevation factor (lower elevation = higher risk)
    if elevation < 50:
        probability += 0.15
    elif elevation < 100:
        probability += 0.05

    # Soil type factor
    soil_factors = {
        'clay': 0.1,      # Poor drainage
        'sand': -0.05,    # Good drainage
        'loam': 0.02,     # Moderate drainage
        'rock': -0.1      # Excellent drainage
    }
    probability += soil_factors.get(soil_type.lower(), 0)

    # Humidity factor
    if humidity > 80:
        probability += 0.05

    # Wind speed factor (high winds can worsen flooding)
    if wind_speed > 20:
        probability += 0.05

    return min(0.95, max(0.05, probability))

def calculate_earthquake_probability(recent_earthquakes, max_magnitude_30d, avg_magnitude,
                                   depth_avg, fault_distance, tectonic_activity, geological_stability):
    """Calculate earthquake probability based on input parameters"""

    # Base probability
    probability = 0.1

    # Recent earthquake activity (most important factor)
    if recent_earthquakes > 10:
        probability += 0.4
    elif recent_earthquakes > 5:
        probability += 0.2
    elif recent_earthquakes > 2:
        probability += 0.1

    # Maximum magnitude factor
    if max_magnitude_30d > 6:
        probability += 0.3
    elif max_magnitude_30d > 4:
        probability += 0.15
    elif max_magnitude_30d > 3:
        probability += 0.05

    # Average magnitude factor
    if avg_magnitude > 4:
        probability += 0.2
    elif avg_magnitude > 3:
        probability += 0.1

    # Fault distance factor (closer = higher risk)
    if fault_distance < 10:
        probability += 0.25
    elif fault_distance < 50:
        probability += 0.1
    elif fault_distance < 100:
        probability += 0.05

    # Tectonic activity factor
    tectonic_factors = {
        'high': 0.2,
        'medium': 0.1,
        'low': 0.0,
        'very_low': -0.05
    }
    probability += tectonic_factors.get(tectonic_activity.lower(), 0)

    # Geological stability factor
    stability_factors = {
        'unstable': 0.15,
        'moderate': 0.05,
        'stable': 0.0,
        'very_stable': -0.05
    }
    probability += stability_factors.get(geological_stability.lower(), 0)

    # Depth factor (shallow earthquakes are more dangerous)
    if depth_avg < 10:
        probability += 0.1
    elif depth_avg > 50:
        probability -= 0.05

    return min(0.9, max(0.05, probability))

def estimate_earthquake_magnitude(max_magnitude_30d, avg_magnitude, recent_earthquakes, fault_distance):
    """Estimate potential earthquake magnitude"""

    # Base magnitude
    magnitude = 4.0

    # Historical magnitude influence
    if max_magnitude_30d > 0:
        magnitude = max(magnitude, max_magnitude_30d * 0.8)

    if avg_magnitude > 0:
        magnitude = max(magnitude, avg_magnitude + 0.5)

    # Recent activity influence
    if recent_earthquakes > 10:
        magnitude += 0.8
    elif recent_earthquakes > 5:
        magnitude += 0.4

    # Fault proximity influence
    if fault_distance < 10:
        magnitude += 0.5
    elif fault_distance < 50:
        magnitude += 0.2

    return min(8.0, max(3.0, magnitude))

def calculate_confidence(prediction_data):
    """Calculate confidence score based on data completeness"""
    total_fields = len(prediction_data)
    filled_fields = sum(1 for v in prediction_data.values() if v is not None and v != "")

    base_confidence = filled_fields / total_fields if total_fields > 0 else 0.5

    # Adjust confidence based on critical fields
    critical_fields = ['latitude', 'longitude']
    critical_filled = sum(1 for field in critical_fields if prediction_data.get(field) is not None)

    if critical_filled == len(critical_fields):
        base_confidence += 0.1

    return min(0.95, max(0.3, base_confidence))

def analyze_flood_factors(data):
    """Analyze and return key factors affecting flood risk"""
    factors = []

    precipitation_24h = float(data.get('precipitation_24h', 0))
    water_level = float(data.get('water_level', 0))
    elevation = float(data.get('elevation', 100))

    if precipitation_24h > 50:
        factors.append("Heavy rainfall in last 24 hours")
    if water_level > 4:
        factors.append("High water levels detected")
    if elevation < 50:
        factors.append("Low elevation area - higher flood risk")

    soil_type = data.get('soil_type', '').lower()
    if soil_type == 'clay':
        factors.append("Clay soil - poor drainage")

    return factors

def analyze_earthquake_factors(data):
    """Analyze and return key factors affecting earthquake risk"""
    factors = []

    recent_earthquakes = int(data.get('recent_earthquakes', 0))
    fault_distance = float(data.get('fault_distance', 100))
    max_magnitude = float(data.get('max_magnitude_30d', 0))

    if recent_earthquakes > 5:
        factors.append("High recent seismic activity")
    if fault_distance < 50:
        factors.append("Close proximity to fault lines")
    if max_magnitude > 5:
        factors.append("Recent significant earthquakes in area")

    tectonic_activity = data.get('tectonic_activity', '').lower()
    if tectonic_activity == 'high':
        factors.append("High tectonic activity region")

    return factors

if __name__ == "__main__":
    print("🌊 Starting Disaster Management System...")
    print("📊 Dashboard: http://localhost:8000/dashboard/")
    print("📚 API Docs: http://localhost:8000/docs")
    print("❤️  Health: http://localhost:8000/health")
    print("🔮 Flood Prediction: http://localhost:8000/api/v1/predict/flood")
    print("🏔️  Earthquake Prediction: http://localhost:8000/api/v1/predict/earthquake")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to avoid the warning
        log_level="info"
    )
# fsdecode(sdf)