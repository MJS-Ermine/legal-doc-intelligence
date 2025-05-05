"""System monitoring for legal document processing platform."""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import psutil
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    """Types of metrics to monitor."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"

class AlertLevel(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class Alert:
    """System alert information."""

    level: AlertLevel
    message: str
    timestamp: datetime
    metric_name: str
    current_value: float
    threshold: float
    context: Optional[Dict[str, Any]] = None

@dataclass
class MetricConfig:
    """Configuration for a monitored metric."""

    name: str
    type: MetricType
    description: str
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None  # For histograms
    alert_thresholds: Optional[Dict[AlertLevel, float]] = None

class SystemMonitor:
    """Comprehensive system monitoring for the legal document platform.

    Features:
    1. Resource monitoring (CPU, memory, disk)
    2. Performance metrics
    3. Error tracking
    4. Custom metrics
    5. Alerting system
    6. Prometheus integration
    """

    def __init__(
        self,
        metrics_port: int = 8000,
        alert_history_size: int = 1000,
        monitoring_interval: float = 5.0
    ):
        """Initialize the monitoring system.

        Args:
            metrics_port: Port for Prometheus metrics endpoint.
            alert_history_size: Maximum number of alerts to keep in history.
            monitoring_interval: Interval between metric collections in seconds.
        """
        self.monitoring_interval = monitoring_interval
        self.alert_history = deque(maxlen=alert_history_size)

        # Initialize metrics
        self._init_metrics()

        # Start Prometheus metrics server
        start_http_server(metrics_port)

        # Start monitoring thread
        self.should_monitor = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()

        logger.info(
            f"System monitor initialized on port {metrics_port} "
            f"with {monitoring_interval}s interval"
        )

    def _init_metrics(self) -> None:
        """Initialize monitoring metrics."""
        # System metrics
        self.metrics = {
            # Resource metrics
            "cpu_usage": Gauge(
                "system_cpu_usage",
                "CPU usage percentage"
            ),
            "memory_usage": Gauge(
                "system_memory_usage_bytes",
                "Memory usage in bytes"
            ),
            "disk_usage": Gauge(
                "system_disk_usage_bytes",
                "Disk usage in bytes"
            ),

            # Document processing metrics
            "docs_processed": Counter(
                "docs_processed_total",
                "Total number of documents processed",
                ["status"]
            ),
            "processing_time": Histogram(
                "doc_processing_seconds",
                "Time taken to process documents",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
            ),
            "validation_errors": Counter(
                "validation_errors_total",
                "Total number of validation errors",
                ["rule_name", "level"]
            ),

            # Pipeline metrics
            "pipeline_stage_time": Histogram(
                "pipeline_stage_seconds",
                "Time taken for each pipeline stage",
                ["stage"],
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
            ),
            "pipeline_errors": Counter(
                "pipeline_errors_total",
                "Total number of pipeline errors",
                ["stage"]
            ),

            # API metrics
            "api_requests": Counter(
                "api_requests_total",
                "Total number of API requests",
                ["endpoint", "method", "status"]
            ),
            "api_latency": Histogram(
                "api_latency_seconds",
                "API endpoint latency",
                ["endpoint"],
                buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
            ),

            # Vector store metrics
            "vector_store_size": Gauge(
                "vector_store_size_total",
                "Total number of vectors in store"
            ),
            "vector_store_latency": Histogram(
                "vector_store_operation_seconds",
                "Vector store operation latency",
                ["operation"],
                buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
            )
        }

        # Alert thresholds
        self.alert_thresholds = {
            "cpu_usage": {
                AlertLevel.WARNING: 80.0,
                AlertLevel.CRITICAL: 90.0
            },
            "memory_usage": {
                AlertLevel.WARNING: 80.0,
                AlertLevel.CRITICAL: 90.0
            },
            "disk_usage": {
                AlertLevel.WARNING: 80.0,
                AlertLevel.CRITICAL: 90.0
            },
            "error_rate": {
                AlertLevel.WARNING: 0.05,
                AlertLevel.CRITICAL: 0.10
            },
            "api_latency": {
                AlertLevel.WARNING: 2.0,
                AlertLevel.CRITICAL: 5.0
            }
        }

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.should_monitor:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                # Update metrics
                self.metrics["cpu_usage"].set(cpu_percent)
                self.metrics["memory_usage"].set(memory.used)
                self.metrics["disk_usage"].set(disk.used)

                # Check for alerts
                self._check_alerts({
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "disk_usage": disk.percent
                })

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")

            time.sleep(self.monitoring_interval)

    def _check_alerts(self, current_values: Dict[str, float]) -> None:
        """Check metrics against alert thresholds.

        Args:
            current_values: Dictionary of current metric values.
        """
        for metric_name, value in current_values.items():
            if metric_name in self.alert_thresholds:
                for level, threshold in self.alert_thresholds[metric_name].items():
                    if value >= threshold:
                        alert = Alert(
                            level=level,
                            message=f"{metric_name} exceeds {level.value} threshold",
                            timestamp=datetime.now(),
                            metric_name=metric_name,
                            current_value=value,
                            threshold=threshold,
                            context={"unit": "%"}
                        )
                        self.alert_history.append(alert)
                        logger.warning(
                            f"Alert: {alert.message} "
                            f"(current: {value:.1f}%, threshold: {threshold:.1f}%)"
                        )

    def record_document_processed(
        self,
        success: bool,
        processing_time: float
    ) -> None:
        """Record document processing metrics.

        Args:
            success: Whether processing was successful.
            processing_time: Time taken to process the document.
        """
        status = "success" if success else "failure"
        self.metrics["docs_processed"].labels(status=status).inc()
        self.metrics["processing_time"].observe(processing_time)

    def record_validation_error(
        self,
        rule_name: str,
        level: str
    ) -> None:
        """Record validation error metrics.

        Args:
            rule_name: Name of the validation rule.
            level: Error severity level.
        """
        self.metrics["validation_errors"].labels(
            rule_name=rule_name,
            level=level
        ).inc()

    def record_pipeline_stage(
        self,
        stage: str,
        duration: float,
        success: bool
    ) -> None:
        """Record pipeline stage metrics.

        Args:
            stage: Pipeline stage name.
            duration: Stage duration in seconds.
            success: Whether the stage completed successfully.
        """
        self.metrics["pipeline_stage_time"].labels(stage=stage).observe(duration)
        if not success:
            self.metrics["pipeline_errors"].labels(stage=stage).inc()

    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status: int,
        latency: float
    ) -> None:
        """Record API request metrics.

        Args:
            endpoint: API endpoint path.
            method: HTTP method.
            status: Response status code.
            latency: Request latency in seconds.
        """
        self.metrics["api_requests"].labels(
            endpoint=endpoint,
            method=method,
            status=status
        ).inc()
        self.metrics["api_latency"].labels(endpoint=endpoint).observe(latency)

    def record_vector_store_operation(
        self,
        operation: str,
        latency: float
    ) -> None:
        """Record vector store operation metrics.

        Args:
            operation: Operation type (e.g., "insert", "search").
            latency: Operation latency in seconds.
        """
        self.metrics["vector_store_latency"].labels(
            operation=operation
        ).observe(latency)

    def update_vector_store_size(self, size: int) -> None:
        """Update vector store size metric.

        Args:
            size: Current number of vectors in store.
        """
        self.metrics["vector_store_size"].set(size)

    def get_recent_alerts(
        self,
        level: Optional[AlertLevel] = None,
        since: Optional[datetime] = None
    ) -> List[Alert]:
        """Get recent alerts with optional filtering.

        Args:
            level: Optional alert level to filter by.
            since: Optional timestamp to filter alerts from.

        Returns:
            List of matching alerts.
        """
        alerts = list(self.alert_history)

        if level:
            alerts = [a for a in alerts if a.level == level]

        if since:
            alerts = [a for a in alerts if a.timestamp >= since]

        return alerts

    def get_error_rate(
        self,
        window_minutes: float = 5.0
    ) -> float:
        """Calculate recent error rate.

        Args:
            window_minutes: Time window in minutes.

        Returns:
            Error rate as a fraction.
        """
        window_start = datetime.now() - timedelta(minutes=window_minutes)
        alerts = self.get_recent_alerts(since=window_start)

        if not alerts:
            return 0.0

        error_alerts = [
            a for a in alerts
            if a.level in (AlertLevel.WARNING, AlertLevel.CRITICAL)
        ]

        return len(error_alerts) / len(alerts)

    def get_performance_stats(
        self,
        window_minutes: float = 5.0
    ) -> Dict[str, Any]:
        """Get recent performance statistics.

        Args:
            window_minutes: Time window in minutes.

        Returns:
            Dictionary of performance statistics.
        """
        # Calculate basic statistics
        api_latencies = [
            sample[0]
            for sample in self.metrics["api_latency"]._samples()
        ]

        processing_times = [
            sample[0]
            for sample in self.metrics["processing_time"]._samples()
        ]

        return {
            "api_latency": {
                "mean": np.mean(api_latencies) if api_latencies else 0.0,
                "p95": np.percentile(api_latencies, 95) if api_latencies else 0.0,
                "max": max(api_latencies) if api_latencies else 0.0
            },
            "processing_time": {
                "mean": np.mean(processing_times) if processing_times else 0.0,
                "p95": np.percentile(processing_times, 95) if processing_times else 0.0,
                "max": max(processing_times) if processing_times else 0.0
            },
            "error_rate": self.get_error_rate(window_minutes),
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }

    def cleanup(self) -> None:
        """Clean up monitoring resources."""
        self.should_monitor = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
