"""Nova 統一資料模型

定義所有模組使用的統一資料結構。
"""

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class Metric:
    """效能指標基類"""

    name: str
    value: Union[int, float]
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PerformanceMetrics:
    """效能測試指標集合"""

    execution_time: Metric
    memory_usage: Metric
    cpu_usage: Optional[Metric] = None
    gpu_usage: Optional[Metric] = None
    io_operations: Optional[Metric] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            "execution_time": self.execution_time.to_dict(),
            "memory_usage": self.memory_usage.to_dict(),
        }

        if self.cpu_usage:
            result["cpu_usage"] = self.cpu_usage.to_dict()
        if self.gpu_usage:
            result["gpu_usage"] = self.gpu_usage.to_dict()
        if self.io_operations:
            result["io_operations"] = self.io_operations.to_dict()

        return result


@dataclass
class TestResult:
    """測試結果"""

    test_name: str
    function_name: str
    module_name: str
    status: str  # 'success', 'failure', 'error'
    metrics: PerformanceMetrics
    iterations: int
    start_time: datetime
    end_time: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """測試持續時間（秒）"""
        return (self.end_time - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "test_name": self.test_name,
            "function_name": self.function_name,
            "module_name": self.module_name,
            "status": self.status,
            "metrics": self.metrics.to_dict(),
            "iterations": self.iterations,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration": self.duration,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class BenchmarkResult:
    """基準測試結果"""

    function_name: str
    iterations: int
    execution_times: List[float]
    memory_usages: List[float]
    cpu_usages: List[float] = field(default_factory=list)
    gpu_usages: List[float] = field(default_factory=list)

    @property
    def avg_execution_time(self) -> float:
        """平均執行時間"""
        return statistics.mean(self.execution_times)

    @property
    def min_execution_time(self) -> float:
        """最小執行時間"""
        return min(self.execution_times)

    @property
    def max_execution_time(self) -> float:
        """最大執行時間"""
        return max(self.execution_times)

    @property
    def std_execution_time(self) -> float:
        """執行時間標準差"""
        return (
            statistics.stdev(self.execution_times)
            if len(self.execution_times) > 1
            else 0.0
        )

    @property
    def avg_memory_usage(self) -> float:
        """平均記憶體使用量"""
        return statistics.mean(self.memory_usages)

    @property
    def avg_cpu_usage(self) -> float:
        """平均 CPU 使用率"""
        return statistics.mean(self.cpu_usages) if self.cpu_usages else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "function_name": self.function_name,
            "iterations": self.iterations,
            "execution_time": {
                "mean": self.avg_execution_time,
                "min": self.min_execution_time,
                "max": self.max_execution_time,
                "std": self.std_execution_time,
            },
            "memory_usage": {
                "mean": self.avg_memory_usage,
                "values": self.memory_usages,
            },
            "cpu_usage": {"mean": self.avg_cpu_usage, "values": self.cpu_usages},
            "gpu_usage": {"values": self.gpu_usages} if self.gpu_usages else {},
        }


@dataclass
class Issue:
    """代碼問題/問題"""

    file_path: Path
    line_number: int
    code: str
    message: str
    issue_type: str = "error"  # 'error', 'warning', 'info'
    column: Optional[int] = None
    rule: Optional[str] = None
    severity: str = "medium"  # 'low', 'medium', 'high', 'critical'
    fix_suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "file_path": str(self.file_path),
            "line_number": self.line_number,
            "column": self.column,
            "issue_type": self.issue_type,
            "code": self.code,
            "message": self.message,
            "rule": self.rule,
            "severity": self.severity,
            "fix_suggestion": self.fix_suggestion,
            "metadata": self.metadata,
        }


@dataclass
class AuditResult:
    """審計結果"""

    target_path: Path
    issues: List[Issue]
    statistics: Dict[str, Any]
    scan_time: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_issues(self) -> int:
        """總問題數"""
        return len(self.issues)

    @property
    def errors_count(self) -> int:
        """錯誤數量"""
        return len([i for i in self.issues if i.issue_type == "error"])

    @property
    def warnings_count(self) -> int:
        """警告數量"""
        return len([i for i in self.issues if i.issue_type == "warning"])

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "target_path": str(self.target_path),
            "issues": [issue.to_dict() for issue in self.issues],
            "statistics": self.statistics,
            "scan_time": self.scan_time.isoformat(),
            "duration": self.duration,
            "summary": {
                "total_issues": self.total_issues,
                "errors": self.errors_count,
                "warnings": self.warnings_count,
            },
            "metadata": self.metadata,
        }


@dataclass
class SystemInfo:
    """系統資訊"""

    platform: str
    python_version: str
    cpu_count: int
    memory_total_gb: float
    gpu_available: bool = False
    gpu_count: int = 0
    gpu_info: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "platform": self.platform,
            "python_version": self.python_version,
            "cpu_count": self.cpu_count,
            "memory_total_gb": self.memory_total_gb,
            "gpu_available": self.gpu_available,
            "gpu_count": self.gpu_count,
            "gpu_info": self.gpu_info,
            "metadata": self.metadata,
        }


@dataclass
class Report:
    """綜合報告"""

    title: str
    report_type: str  # 'performance', 'audit', 'monitoring', 'system'
    generated_at: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "title": self.title,
            "report_type": self.report_type,
            "generated_at": self.generated_at.isoformat(),
            "data": self.data,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }
