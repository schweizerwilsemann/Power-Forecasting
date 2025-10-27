from __future__ import annotations

import psutil
import time
from datetime import datetime
from typing import Dict, Any

from ..domain.interfaces import ModelGateway


class MonitoringService:
    """Service for system monitoring and health checks."""
    
    def __init__(self, model_gateway: ModelGateway):
        self.model_gateway = model_gateway
        self.start_time = time.time()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
            
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Uptime
            uptime = time.time() - self.start_time
            
            # Model status
            model_loaded = self.model_gateway.is_ready()
            
            # Database connection (simplified check)
            database_connected = True  # In real implementation, check actual DB connection
            
            return {
                "status": "healthy" if model_loaded and database_connected else "degraded",
                "timestamp": datetime.now(),
                "model_loaded": model_loaded,
                "database_connected": database_connected,
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "uptime": uptime
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(),
                "model_loaded": False,
                "database_connected": False,
                "memory_usage": {},
                "cpu_usage": 0.0,
                "uptime": 0.0,
                "error": str(e)
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the system."""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk_usage = psutil.disk_usage('/')
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                "system": {
                    "memory_percent": memory.percent,
                    "cpu_percent": cpu_percent,
                    "disk_percent": (disk_usage.used / disk_usage.total) * 100
                },
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process_cpu
                },
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now()
            }
