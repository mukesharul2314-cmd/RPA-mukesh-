// Dashboard JavaScript
class DisasterDashboard {
    constructor() {
        this.map = null;
        this.layers = {
            earthquakes: null,
            floods: null,
            alerts: null
        };
        this.apiBaseUrl = '/api/v1';
        this.refreshInterval = 30000; // 30 seconds
        
        this.init();
    }
    
    init() {
        this.initMap();
        this.loadDashboardData();
        this.setupEventListeners();
        this.startAutoRefresh();
    }
    
    initMap() {
        // Initialize Leaflet map
        this.map = L.map('map').setView([39.8283, -98.5795], 4); // Center on USA
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
        
        // Initialize layer groups
        this.layers.earthquakes = L.layerGroup().addTo(this.map);
        this.layers.floods = L.layerGroup().addTo(this.map);
        this.layers.alerts = L.layerGroup().addTo(this.map);
        
        // Map click handler for predictions
        this.map.on('click', (e) => {
            const lat = e.latlng.lat.toFixed(6);
            const lon = e.latlng.lng.toFixed(6);
            
            document.getElementById('flood-lat').value = lat;
            document.getElementById('flood-lon').value = lon;
            document.getElementById('earthquake-lat').value = lat;
            document.getElementById('earthquake-lon').value = lon;
        });
    }
    
    async loadDashboardData() {
        try {
            // Load dashboard summary
            const response = await fetch(`${this.apiBaseUrl}/dashboard/summary`);
            const data = await response.json();
            
            this.updateDashboardStats(data);
            this.updateRecentAlerts(data.active_alerts);
            this.updateWeatherSummary(data.weather_summary);
            this.updateSeismicActivity(data.seismic_activity);
            this.updateMapData();
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    updateDashboardStats(data) {
        // Update overview cards
        document.getElementById('active-alerts-count').textContent = data.active_alerts.length;
        document.getElementById('flood-predictions-count').textContent = data.recent_predictions.flood.length;
        document.getElementById('earthquake-predictions-count').textContent = data.recent_predictions.earthquake.length;
        
        // Update system status
        const statusElement = document.getElementById('system-status');
        const status = data.system_status.status;
        statusElement.className = `badge bg-${status === 'operational' ? 'success' : 'warning'}`;
        statusElement.innerHTML = `<i class="fas fa-circle"></i> ${status.charAt(0).toUpperCase() + status.slice(1)}`;
    }
    
    updateRecentAlerts(alerts) {
        const container = document.getElementById('recent-alerts');
        container.innerHTML = '';
        
        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No active alerts</p>';
            return;
        }
        
        alerts.slice(0, 5).forEach(alert => {
            const alertElement = document.createElement('div');
            alertElement.className = `alert-item ${alert.severity.toLowerCase()}`;
            alertElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <strong>${alert.title}</strong>
                        <br>
                        <small class="text-muted">
                            ${alert.alert_type} • ${this.formatDate(alert.created_at)}
                        </small>
                    </div>
                    <span class="badge bg-${this.getSeverityColor(alert.severity)}">
                        ${alert.severity}
                    </span>
                </div>
            `;
            container.appendChild(alertElement);
        });
    }
    
    updateWeatherSummary(weather) {
        if (!weather || Object.keys(weather).length === 0) {
            return;
        }
        
        document.getElementById('avg-temperature').textContent = 
            weather.average_temperature ? `${weather.average_temperature.toFixed(1)}°C` : '--°C';
        document.getElementById('avg-humidity').textContent = 
            weather.average_humidity ? `${weather.average_humidity.toFixed(0)}%` : '--%';
        document.getElementById('total-precipitation').textContent = 
            weather.total_precipitation ? `${weather.total_precipitation.toFixed(1)} mm` : '-- mm';
        document.getElementById('max-wind-speed').textContent = 
            weather.max_wind_speed ? `${weather.max_wind_speed.toFixed(1)} m/s` : '-- m/s';
    }
    
    updateSeismicActivity(earthquakes) {
        const container = document.getElementById('recent-earthquakes');
        container.innerHTML = '';
        
        if (earthquakes.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No recent earthquakes</p>';
            return;
        }
        
        earthquakes.slice(0, 5).forEach(eq => {
            const eqElement = document.createElement('div');
            eqElement.className = 'earthquake-item';
            eqElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <span class="magnitude ${this.getMagnitudeClass(eq.magnitude)}">
                            M${eq.magnitude.toFixed(1)}
                        </span>
                        <div class="mt-1">
                            <small>${eq.place || 'Unknown location'}</small>
                            <br>
                            <small class="text-muted">${this.formatDate(eq.timestamp)}</small>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="dashboard.centerMapOn(${eq.latitude}, ${eq.longitude})">
                        <i class="fas fa-map-marker-alt"></i>
                    </button>
                </div>
            `;
            container.appendChild(eqElement);
        });
    }
    
    async updateMapData() {
        try {
            // Get map bounds
            const bounds = this.map.getBounds();
            const center = this.map.getCenter();
            
            const response = await fetch(
                `${this.apiBaseUrl}/dashboard/map-data?latitude=${center.lat}&longitude=${center.lng}&radius_km=1000`
            );
            const data = await response.json();
            
            this.updateEarthquakeMarkers(data.earthquakes);
            this.updateFloodMarkers(data.flood_predictions);
            this.updateAlertMarkers(data.alerts);
            
        } catch (error) {
            console.error('Error loading map data:', error);
        }
    }
    
    updateEarthquakeMarkers(earthquakes) {
        this.layers.earthquakes.clearLayers();
        
        earthquakes.forEach(eq => {
            const size = this.getEarthquakeMarkerSize(eq.magnitude);
            const color = this.getEarthquakeColor(eq.magnitude);
            
            const marker = L.circleMarker([eq.latitude, eq.longitude], {
                radius: size,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            });
            
            marker.bindPopup(`
                <strong>Earthquake M${eq.magnitude.toFixed(1)}</strong><br>
                <strong>Location:</strong> ${eq.place || 'Unknown'}<br>
                <strong>Depth:</strong> ${eq.depth ? eq.depth.toFixed(1) + ' km' : 'Unknown'}<br>
                <strong>Time:</strong> ${this.formatDate(eq.timestamp)}
            `);
            
            this.layers.earthquakes.addLayer(marker);
        });
    }
    
    updateFloodMarkers(predictions) {
        this.layers.floods.clearLayers();
        
        predictions.forEach(pred => {
            const color = this.getRiskColor(pred.risk_level);
            
            const marker = L.circleMarker([pred.latitude, pred.longitude], {
                radius: 8,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.7
            });
            
            marker.bindPopup(`
                <strong>Flood Prediction</strong><br>
                <strong>Risk Level:</strong> ${pred.risk_level}<br>
                <strong>Probability:</strong> ${(pred.probability * 100).toFixed(1)}%<br>
                <strong>Prediction Time:</strong> ${this.formatDate(pred.prediction_time)}
            `);
            
            this.layers.floods.addLayer(marker);
        });
    }
    
    updateAlertMarkers(alerts) {
        this.layers.alerts.clearLayers();
        
        alerts.forEach(alert => {
            const color = this.getSeverityColor(alert.severity);
            
            const marker = L.marker([alert.latitude, alert.longitude], {
                icon: L.divIcon({
                    className: 'alert-marker',
                    html: `<div style="background-color: ${color}; width: 20px; height: 20px; transform: rotate(45deg);"></div>`,
                    iconSize: [20, 20],
                    iconAnchor: [10, 10]
                })
            });
            
            marker.bindPopup(`
                <strong>${alert.title}</strong><br>
                <strong>Type:</strong> ${alert.alert_type}<br>
                <strong>Severity:</strong> ${alert.severity}<br>
                <strong>Created:</strong> ${this.formatDate(alert.created_at)}
            `);
            
            this.layers.alerts.addLayer(marker);
        });
    }
    
    setupEventListeners() {
        // Flood prediction form
        document.getElementById('flood-prediction-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.generateFloodPrediction();
        });
        
        // Earthquake prediction form
        document.getElementById('earthquake-prediction-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.generateEarthquakePrediction();
        });
    }
    
    async generateFloodPrediction() {
        const lat = parseFloat(document.getElementById('flood-lat').value);
        const lon = parseFloat(document.getElementById('flood-lon').value);
        const hours = parseInt(document.getElementById('flood-hours').value);
        
        const resultContainer = document.getElementById('flood-prediction-result');
        resultContainer.innerHTML = '<div class="loading"></div> Generating prediction...';
        resultContainer.classList.remove('d-none');
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/predictions/flood`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    latitude: lat,
                    longitude: lon,
                    hours_ahead: hours
                })
            });
            
            const prediction = await response.json();
            
            resultContainer.innerHTML = `
                <div class="prediction-result">
                    <h6>Flood Prediction Result</h6>
                    <div class="risk-level ${prediction.risk_level}">
                        Risk Level: ${prediction.risk_level}
                    </div>
                    <p><strong>Probability:</strong> ${(prediction.flood_probability * 100).toFixed(1)}%</p>
                    <p><strong>Confidence:</strong> ${(prediction.confidence_score * 100).toFixed(1)}%</p>
                    <p><strong>Prediction Time:</strong> ${this.formatDate(prediction.prediction_time)}</p>
                </div>
            `;
            
            // Add marker to map
            const marker = L.marker([lat, lon]).addTo(this.map);
            marker.bindPopup(`
                <strong>Flood Prediction</strong><br>
                Risk: ${prediction.risk_level}<br>
                Probability: ${(prediction.flood_probability * 100).toFixed(1)}%
            `).openPopup();
            
        } catch (error) {
            console.error('Error generating flood prediction:', error);
            resultContainer.innerHTML = '<div class="alert alert-danger">Error generating prediction</div>';
        }
    }
    
    async generateEarthquakePrediction() {
        const lat = parseFloat(document.getElementById('earthquake-lat').value);
        const lon = parseFloat(document.getElementById('earthquake-lon').value);
        const hours = parseInt(document.getElementById('earthquake-hours').value);
        
        const resultContainer = document.getElementById('earthquake-prediction-result');
        resultContainer.innerHTML = '<div class="loading"></div> Assessing risk...';
        resultContainer.classList.remove('d-none');
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/predictions/earthquake`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    latitude: lat,
                    longitude: lon,
                    hours_ahead: hours
                })
            });
            
            const prediction = await response.json();
            
            resultContainer.innerHTML = `
                <div class="prediction-result">
                    <h6>Earthquake Risk Assessment</h6>
                    <div class="risk-level ${prediction.risk_level}">
                        Risk Level: ${prediction.risk_level}
                    </div>
                    <p><strong>Risk Probability:</strong> ${(prediction.risk_probability * 100).toFixed(1)}%</p>
                    <p><strong>Estimated Magnitude:</strong> M${prediction.estimated_magnitude.toFixed(1)}</p>
                    <p><strong>Confidence:</strong> ${(prediction.confidence_score * 100).toFixed(1)}%</p>
                    <p><strong>Assessment Time:</strong> ${this.formatDate(prediction.prediction_time)}</p>
                </div>
            `;
            
            // Add marker to map
            const marker = L.marker([lat, lon]).addTo(this.map);
            marker.bindPopup(`
                <strong>Earthquake Risk</strong><br>
                Risk: ${prediction.risk_level}<br>
                Probability: ${(prediction.risk_probability * 100).toFixed(1)}%
            `).openPopup();
            
        } catch (error) {
            console.error('Error generating earthquake prediction:', error);
            resultContainer.innerHTML = '<div class="alert alert-danger">Error assessing risk</div>';
        }
    }
    
    startAutoRefresh() {
        setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
    }
    
    // Utility methods
    centerMapOn(lat, lon) {
        this.map.setView([lat, lon], 8);
    }
    
    toggleLayer(layerName) {
        const layer = this.layers[layerName];
        if (this.map.hasLayer(layer)) {
            this.map.removeLayer(layer);
        } else {
            this.map.addLayer(layer);
        }
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    getMagnitudeClass(magnitude) {
        if (magnitude < 4) return 'low';
        if (magnitude < 5) return 'moderate';
        if (magnitude < 6) return 'strong';
        return 'major';
    }
    
    getEarthquakeMarkerSize(magnitude) {
        return Math.max(4, Math.min(20, magnitude * 3));
    }
    
    getEarthquakeColor(magnitude) {
        if (magnitude < 4) return '#28a745';
        if (magnitude < 5) return '#ffc107';
        if (magnitude < 6) return '#fd7e14';
        return '#dc3545';
    }
    
    getRiskColor(riskLevel) {
        const colors = {
            'LOW': '#28a745',
            'MEDIUM': '#ffc107',
            'HIGH': '#fd7e14',
            'CRITICAL': '#dc3545'
        };
        return colors[riskLevel] || '#6c757d';
    }
    
    getSeverityColor(severity) {
        const colors = {
            'LOW': 'success',
            'MEDIUM': 'warning',
            'HIGH': 'warning',
            'CRITICAL': 'danger'
        };
        return colors[severity] || 'secondary';
    }
    
    showError(message) {
        const alertBanner = document.getElementById('alert-banner');
        document.getElementById('alert-message').textContent = message;
        alertBanner.classList.remove('d-none');
    }
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new DisasterDashboard();
});

// Global functions for HTML onclick handlers
function toggleLayer(layerName) {
    if (dashboard) {
        dashboard.toggleLayer(layerName);
    }
}
