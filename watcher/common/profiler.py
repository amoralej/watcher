# Copyright (c) 2025 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Profiler utilities for Watcher audit operations."""

import functools

import psutil
from oslo_config import cfg
from oslo_log import log
from osprofiler import profiler

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class MemoryTracker:
    """Context manager for tracking memory usage during operations."""

    def __init__(self, trace_name, audit_id=None):
        """Initialize memory tracker.

        :param trace_name: Name for the profiler trace point
        :param audit_id: Optional audit UUID for correlation
        """
        self.trace_name = trace_name
        self.audit_id = audit_id
        self.process = psutil.Process()
        self.mem_baseline = None
        self.mem_peak = None

    def __enter__(self):
        """Capture baseline memory on enter."""
        if CONF.profiler.trace_memory_usage:
            try:
                self.mem_baseline = self.process.memory_info().rss / 1024 / 1024  # MB
            except Exception as e:
                LOG.warning("Failed to capture baseline memory: %s", e)
                self.mem_baseline = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Capture peak memory and attach to trace on exit."""
        if CONF.profiler.trace_memory_usage and self.mem_baseline is not None:
            try:
                self.mem_peak = self.process.memory_info().rss / 1024 / 1024  # MB
                mem_delta = self.mem_peak - self.mem_baseline

                # Attach memory metrics to current trace
                profiler.stop({
                    "memory_baseline_mb": self.mem_baseline,
                    "memory_peak_mb": self.mem_peak,
                    "memory_delta_mb": mem_delta,
                    "audit_id": str(self.audit_id) if self.audit_id else None
                })
            except Exception as e:
                LOG.warning("Failed to capture peak memory: %s", e)

        return False  # Don't suppress exceptions


def trace_with_memory(name, info=None):
    """Decorator combining @profiler.trace() with memory tracking.

    Usage:
        @trace_with_memory("watcher-audit-execute",
                          info=lambda audit: {"audit_id": audit.uuid})
        def execute(self, audit, context):
            # Your code here
            pass

    :param name: Trace point name (e.g., "watcher-audit-execute")
    :param info: Dict or callable returning dict with trace metadata
    """
    def decorator(func):
        # First apply osprofiler decorator for timing
        traced_func = profiler.trace(name, info=info)(func)

        @functools.wraps(traced_func)
        def wrapper(*args, **kwargs):
            # Extract audit_id if available
            audit_id = None
            if info and callable(info):
                try:
                    metadata = info(*args, **kwargs)
                    audit_id = metadata.get('audit_id')
                except Exception:
                    pass

            # Execute with memory tracking
            with MemoryTracker(name, audit_id):
                return traced_func(*args, **kwargs)

        return wrapper
    return decorator


def is_profiling_enabled():
    """Check if profiling is currently enabled."""
    return CONF.profiler.enabled and profiler.get() is not None
