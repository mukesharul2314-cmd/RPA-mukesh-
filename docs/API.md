# API Documentation

## Overview

The Disaster Management Predictive Analytics API provides endpoints for:
- Weather, seismic, and river gauge data management
- Flood and earthquake predictions
- Alert management
- Dashboard data and analytics

Base URL: `http://localhost:8000/api/v1`

## Authentication

Currently, the API does not require authentication for development. In production, implement appropriate authentication mechanisms.

## Endpoints

### Health and Status

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/status
System status and statistics.

**Response:**
```json
{
  "system_status": "operational",
  "data_counts": {
    "weather_records": 1500,
    "seismic_records": 250,
    "flood_predictions": 45,
    "earthquake_predictions": 30,
    "active_alerts": 3
  },
  "recent_activity": {
    "weather_records_24h": 120,
    "seismic_records_24h": 8
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Data Management

#### POST /api/v1/data/weather
Create weather data record.

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "temperature": 20.5,
  "humidity": 65.0,
  "pressure": 1013.25,
  "precipitation": 0.0,
  "wind_speed": 5.2,
  "wind_direction": 180.0,
  "visibility": 10.0,
  "source": "openweathermap"
}
```

#### GET /api/v1/data/weather
Retrieve weather data with optional filters.

**Query Parameters:**
- `latitude` (float): Latitude for location filter
- `longitude` (float): Longitude for location filter
- `radius_km` (float): Radius in kilometers (default: 50)
- `hours` (int): Hours of historical data (default: 24)
- `limit` (int): Maximum records to return (default: 100)

#### POST /api/v1/data/seismic
Create seismic data record.

**Request Body:**
```json
{
  "event_id": "us7000abcd",
  "timestamp": "2024-01-01T12:00:00Z",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "magnitude": 4.5,
  "depth": 10.0,
  "magnitude_type": "Mw",
  "place": "San Francisco Bay Area",
  "source": "usgs"
}
```

#### GET /api/v1/data/seismic
Retrieve seismic data with optional filters.

**Query Parameters:**
- `latitude` (float): Latitude for location filter
- `longitude` (float): Longitude for location filter
- `radius_km` (float): Radius in kilometers (default: 500)
- `days` (int): Days of historical data (default: 30)
- `min_magnitude` (float): Minimum magnitude (default: 2.0)
- `limit` (int): Maximum records to return (default: 100)

### Predictions

#### POST /api/v1/predictions/flood
Generate flood prediction.

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "hours_ahead": 24
}
```

**Response:**
```json
{
  "id": 123,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "flood_probability": 0.65,
  "risk_level": "HIGH",
  "confidence_score": 0.8,
  "prediction_time": "2024-01-02T12:00:00Z",
  "model_version": "1.0",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### POST /api/v1/predictions/earthquake
Generate earthquake risk assessment.

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "hours_ahead": 72
}
```

**Response:**
```json
{
  "id": 124,
  "latitude": 37.7749,
  "longitude": -122.4194,
  "risk_probability": 0.45,
  "estimated_magnitude": 5.2,
  "risk_level": "MEDIUM",
  "confidence_score": 0.7,
  "prediction_time": "2024-01-04T12:00:00Z",
  "model_version": "1.0",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/predictions/flood/recent
Get recent flood predictions.

**Query Parameters:**
- `limit` (int): Maximum records (default: 10)
- `latitude` (float): Location filter
- `longitude` (float): Location filter
- `radius_km` (float): Radius filter (default: 100)

#### GET /api/v1/predictions/earthquake/recent
Get recent earthquake predictions.

**Query Parameters:**
- `limit` (int): Maximum records (default: 10)
- `latitude` (float): Location filter
- `longitude` (float): Location filter
- `radius_km` (float): Radius filter (default: 100)

### Alerts

#### POST /api/v1/alerts/
Create an alert.

**Request Body:**
```json
{
  "alert_type": "FLOOD",
  "severity": "HIGH",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "title": "Flood Warning",
  "message": "High flood risk detected in the area.",
  "expires_at": "2024-01-02T12:00:00Z"
}
```

#### GET /api/v1/alerts/
Get alerts with optional filters.

**Query Parameters:**
- `active_only` (bool): Only active alerts (default: true)
- `alert_type` (str): Filter by type (FLOOD, EARTHQUAKE)
- `severity` (str): Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)
- `latitude` (float): Location filter
- `longitude` (float): Location filter
- `radius_km` (float): Radius filter (default: 100)
- `limit` (int): Maximum records (default: 50)

#### GET /api/v1/alerts/{alert_id}
Get specific alert by ID.

#### PUT /api/v1/alerts/{alert_id}/deactivate
Deactivate an alert.

#### DELETE /api/v1/alerts/{alert_id}
Delete an alert.

### Dashboard

#### GET /api/v1/dashboard/summary
Get dashboard summary data.

**Response:**
```json
{
  "active_alerts": [...],
  "recent_predictions": {
    "flood": [...],
    "earthquake": [...]
  },
  "weather_summary": {
    "average_temperature": 22.5,
    "average_humidity": 65.0,
    "total_precipitation": 5.2,
    "max_wind_speed": 12.3
  },
  "seismic_activity": [...],
  "system_status": {
    "status": "operational",
    "data_freshness": {...},
    "active_components": {...}
  }
}
```

#### GET /api/v1/dashboard/map-data
Get map data for visualization.

**Query Parameters:**
- `latitude` (float, required): Center latitude
- `longitude` (float, required): Center longitude
- `radius_km` (float): Radius in kilometers (default: 500)

#### GET /api/v1/dashboard/analytics
Get analytics data for charts.

**Query Parameters:**
- `days` (int): Number of days for analysis (default: 30)

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error description"
}
```

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

## Data Formats

### Coordinates
- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees

### Risk Levels
- `LOW`: Low risk
- `MEDIUM`: Medium risk
- `HIGH`: High risk
- `CRITICAL`: Critical risk

### Alert Types
- `FLOOD`: Flood-related alerts
- `EARTHQUAKE`: Earthquake-related alerts
- `WEATHER`: Weather-related alerts

### Timestamps
All timestamps are in ISO 8601 format (UTC): `YYYY-MM-DDTHH:MM:SSZ`
