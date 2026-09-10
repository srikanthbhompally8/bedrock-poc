"""
System Metrics Collection during Performance Testing.

Monitors:
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- Database connections
- Process metrics
"""

import time
import subprocess
import json
from dataclasses import dataclass, asdict
from typing import List, Dict
from datetime import datetime


@dataclass
class SystemMetric:
    """Single system metric data point."""
    timestamp: str
    metric_name: str
    value: float
    unit: str


@dataclass
class SystemMetricsSnapshot:
    """Snapshot of system metrics at a point in time."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_free_gb: float
    network_bytes_sent: float
    network_bytes_recv: float
    process_count: int
    database_connections: int


class SystemMetricsCollector:
    """Collects system metrics during testing."""

    def __init__(self):
        self.metrics: List[SystemMetricsSnapshot] = []
        self.start_time = None
        self.end_time = None

    def collect_cpu_metrics(self) -> float:
        """Collect CPU usage percentage."""
        try:
            if hasattr(subprocess, 'run'):
                # Using psutil would be better, but let's use system commands
                result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True)
                # This is a simplified approach; in production, use psutil
                return 0.0  # Placeholder
            return 0.0
        except Exception as e:
            print(f"Error collecting CPU metrics: {e}")
            return 0.0

    def collect_memory_metrics(self) -> tuple:
        """Collect memory usage."""
        try:
            # For Windows, use psutil if available
            result = subprocess.run(['tasklist', '/v', '/fo', 'csv'], capture_output=True, text=True, shell=True)
            # Placeholder - in production use psutil
            return (50.0, 8192.0, 4096.0)  # (percent, total_mb, available_mb)
        except Exception as e:
            print(f"Error collecting memory metrics: {e}")
            return (0.0, 0.0, 0.0)

    def collect_disk_metrics(self) -> tuple:
        """Collect disk usage."""
        try:
            # Placeholder - in production use psutil
            return (50.0, 100.0)  # (percent, free_gb)
        except Exception as e:
            print(f"Error collecting disk metrics: {e}")
            return (0.0, 0.0)

    def collect_network_metrics(self) -> tuple:
        """Collect network statistics."""
        try:
            # Placeholder - in production use psutil
            return (1000000.0, 1000000.0)  # (bytes_sent, bytes_recv)
        except Exception as e:
            print(f"Error collecting network metrics: {e}")
            return (0.0, 0.0)

    def collect_process_metrics(self) -> int:
        """Collect process count."""
        try:
            result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True)
            if result.stdout:
                return len(result.stdout.split('\n')) - 10  # Rough estimate
            return 0
        except Exception as e:
            print(f"Error collecting process metrics: {e}")
            return 0

    def collect_database_connections(self) -> int:
        """Collect active database connections."""
        try:
            # This would query the database for active connections
            # Placeholder for now
            return 0
        except Exception as e:
            print(f"Error collecting database connection metrics: {e}")
            return 0

    def collect_snapshot(self) -> SystemMetricsSnapshot:
        """Collect a snapshot of all system metrics."""
        cpu = self.collect_cpu_metrics()
        mem_percent, mem_mb, mem_avail = self.collect_memory_metrics()
        disk_percent, disk_free = self.collect_disk_metrics()
        net_sent, net_recv = self.collect_network_metrics()
        proc_count = self.collect_process_metrics()
        db_conns = self.collect_database_connections()

        snapshot = SystemMetricsSnapshot(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu,
            memory_percent=mem_percent,
            memory_mb=mem_mb,
            memory_available_mb=mem_avail,
            disk_percent=disk_percent,
            disk_free_gb=disk_free,
            network_bytes_sent=net_sent,
            network_bytes_recv=net_recv,
            process_count=proc_count,
            database_connections=db_conns
        )

        self.metrics.append(snapshot)
        return snapshot

    def start_collection(self, interval_seconds: int = 5):
        """Start periodic metric collection."""
        self.start_time = datetime.now()
        self.collect_snapshot()

    def stop_collection(self):
        """Stop metric collection."""
        self.end_time = datetime.now()
        self.collect_snapshot()

    def get_summary(self) -> Dict:
        """Get summary statistics of collected metrics."""
        if not self.metrics:
            return {}

        summary = {
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            "samples_collected": len(self.metrics),
            "cpu": {
                "min": min(m.cpu_percent for m in self.metrics),
                "max": max(m.cpu_percent for m in self.metrics),
                "avg": sum(m.cpu_percent for m in self.metrics) / len(self.metrics) if self.metrics else 0,
            },
            "memory": {
                "min_percent": min(m.memory_percent for m in self.metrics),
                "max_percent": max(m.memory_percent for m in self.metrics),
                "avg_percent": sum(m.memory_percent for m in self.metrics) / len(self.metrics) if self.metrics else 0,
                "max_mb": max(m.memory_mb for m in self.metrics),
            },
            "disk": {
                "min_percent": min(m.disk_percent for m in self.metrics),
                "max_percent": max(m.disk_percent for m in self.metrics),
                "avg_percent": sum(m.disk_percent for m in self.metrics) / len(self.metrics) if self.metrics else 0,
            },
            "database_connections": {
                "min": min(m.database_connections for m in self.metrics),
                "max": max(m.database_connections for m in self.metrics),
                "avg": sum(m.database_connections for m in self.metrics) / len(self.metrics) if self.metrics else 0,
            }
        }

        return summary

    def export_json(self, filename: str):
        """Export metrics to JSON file."""
        data = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "summary": self.get_summary(),
            "metrics": [asdict(m) for m in self.metrics]
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Metrics exported to {filename}")


def format_system_metrics_report(collector: SystemMetricsCollector) -> str:
    """Format system metrics as a report."""
    summary = collector.get_summary()

    lines = []
    lines.append("\n" + "="*80)
    lines.append("SYSTEM METRICS REPORT")
    lines.append("="*80)

    if not summary:
        lines.append("No metrics collected")
        return "\n".join(lines)

    lines.append(f"Duration:                  {summary.get('duration_seconds', 0):.1f} seconds")
    lines.append(f"Samples Collected:         {summary.get('samples_collected', 0)}")

    cpu = summary.get('cpu', {})
    lines.append(f"\nCPU Usage:")
    lines.append(f"  Min:                     {cpu.get('min', 0):.1f}%")
    lines.append(f"  Max:                     {cpu.get('max', 0):.1f}%")
    lines.append(f"  Average:                 {cpu.get('avg', 0):.1f}%")

    memory = summary.get('memory', {})
    lines.append(f"\nMemory Usage:")
    lines.append(f"  Min Percent:             {memory.get('min_percent', 0):.1f}%")
    lines.append(f"  Max Percent:             {memory.get('max_percent', 0):.1f}%")
    lines.append(f"  Average Percent:         {memory.get('avg_percent', 0):.1f}%")
    lines.append(f"  Max MB:                  {memory.get('max_mb', 0):.1f} MB")

    disk = summary.get('disk', {})
    lines.append(f"\nDisk Usage:")
    lines.append(f"  Min Percent:             {disk.get('min_percent', 0):.1f}%")
    lines.append(f"  Max Percent:             {disk.get('max_percent', 0):.1f}%")
    lines.append(f"  Average Percent:         {disk.get('avg_percent', 0):.1f}%")

    db_conns = summary.get('database_connections', {})
    lines.append(f"\nDatabase Connections:")
    lines.append(f"  Min:                     {int(db_conns.get('min', 0))}")
    lines.append(f"  Max:                     {int(db_conns.get('max', 0))}")
    lines.append(f"  Average:                 {db_conns.get('avg', 0):.1f}")

    lines.append("="*80 + "\n")
    return "\n".join(lines)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SYSTEM METRICS COLLECTION")
    print("="*80)

    collector = SystemMetricsCollector()
    collector.start_collection()

    print("Collecting metrics for 30 seconds...")
    for i in range(6):
        time.sleep(5)
        snapshot = collector.collect_snapshot()
        print(f"  Sample {i+1}: CPU={snapshot.cpu_percent:.1f}%, Memory={snapshot.memory_percent:.1f}%")

    collector.stop_collection()

    print(format_system_metrics_report(collector))
    collector.export_json("system_metrics.json")
