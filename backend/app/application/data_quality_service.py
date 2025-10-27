from __future__ import annotations

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List
from sklearn.ensemble import IsolationForest

from ..domain.interfaces import HistoryGateway


class DataQualityService:
    """Service for data quality assessment and anomaly detection."""
    
    def __init__(self, history_repository: HistoryGateway):
        self.history_repository = history_repository
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
    
    def assess_data_quality(self) -> Dict[str, Any]:
        """Assess the quality of historical data."""
        try:
            # Get recent data for analysis
            data = self.history_repository.load(limit=1000)
            if data.empty:
                return {
                    "total_records": 0,
                    "missing_values": {},
                    "data_completeness": 0.0,
                    "anomaly_count": 0,
                    "quality_score": 0.0,
                    "last_updated": datetime.now()
                }
            
            # Calculate missing values
            missing_values = data.isnull().sum().to_dict()
            
            # Calculate data completeness
            total_cells = data.size
            missing_cells = data.isnull().sum().sum()
            data_completeness = ((total_cells - missing_cells) / total_cells) * 100
            
            # Detect anomalies
            anomaly_count = self._detect_anomalies(data)
            
            # Calculate quality score (0-100)
            quality_score = self._calculate_quality_score(data_completeness, anomaly_count, missing_values)
            
            return {
                "total_records": len(data),
                "missing_values": missing_values,
                "data_completeness": round(data_completeness, 2),
                "anomaly_count": anomaly_count,
                "quality_score": round(quality_score, 2),
                "last_updated": datetime.now()
            }
        except Exception as e:
            return {
                "total_records": 0,
                "missing_values": {},
                "data_completeness": 0.0,
                "anomaly_count": 0,
                "quality_score": 0.0,
                "last_updated": datetime.now(),
                "error": str(e)
            }
    
    def _detect_anomalies(self, data: pd.DataFrame) -> int:
        """Detect anomalies in the data using Isolation Forest."""
        try:
            # Select numeric columns for anomaly detection
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return 0
            
            # Remove rows with NaN values for anomaly detection
            clean_data = data[numeric_cols].dropna()
            if len(clean_data) == 0:
                return 0
            
            # Fit anomaly detector
            self.anomaly_detector.fit(clean_data)
            
            # Predict anomalies
            anomaly_predictions = self.anomaly_detector.predict(clean_data)
            anomaly_count = sum(1 for pred in anomaly_predictions if pred == -1)
            
            return anomaly_count
        except Exception:
            return 0
    
    def _calculate_quality_score(self, completeness: float, anomaly_count: int, missing_values: Dict[str, int]) -> float:
        """Calculate overall data quality score."""
        # Base score from completeness
        base_score = completeness
        
        # Penalty for anomalies (max 20 points)
        anomaly_penalty = min(20, anomaly_count * 0.1)
        
        # Penalty for missing values in critical columns
        critical_columns = ['Energy delta[Wh]', 'GHI', 'temp']
        missing_penalty = 0
        for col in critical_columns:
            if col in missing_values and missing_values[col] > 0:
                missing_penalty += 5
        
        # Calculate final score
        quality_score = max(0, base_score - anomaly_penalty - missing_penalty)
        return min(100, quality_score)
    
    def validate_import_data(self, data: pd.DataFrame, validation_rules: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate imported data against quality rules."""
        errors = []
        warnings = []
        
        # Required columns check
        required_columns = ['Time', 'Energy delta[Wh]', 'GHI', 'temp']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Data type validation
        if 'Time' in data.columns:
            try:
                pd.to_datetime(data['Time'], dayfirst=True)
            except Exception:
                errors.append("Time column contains invalid datetime values")
        
        # Range validation for numeric columns
        numeric_ranges = {
            'Energy delta[Wh]': (0, 10000),  # Reasonable range for 15-min energy
            'GHI': (0, 1500),  # Global Horizontal Irradiance range
            'temp': (-50, 60),  # Temperature range
            'humidity': (0, 100),  # Humidity percentage
            'pressure': (800, 1200),  # Atmospheric pressure range
        }
        
        for col, (min_val, max_val) in numeric_ranges.items():
            if col in data.columns:
                invalid_values = data[(data[col] < min_val) | (data[col] > max_val)]
                if len(invalid_values) > 0:
                    warnings.append(f"Column {col} has {len(invalid_values)} values outside expected range ({min_val}-{max_val})")
        
        # Missing data check
        missing_data = data.isnull().sum()
        high_missing = missing_data[missing_data > len(data) * 0.1]  # More than 10% missing
        for col, count in high_missing.items():
            warnings.append(f"Column {col} has {count} missing values ({count/len(data)*100:.1f}%)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "quality_score": self._calculate_quality_score(
                (1 - data.isnull().sum().sum() / data.size) * 100,
                self._detect_anomalies(data),
                missing_data.to_dict()
            )
        }
