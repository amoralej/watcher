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

"""Profiler configuration options for Watcher."""

from oslo_config import cfg
from osprofiler import opts as profiler_opts

# Register standard osprofiler options
profiler_opts.set_defaults(cfg.CONF)

# Define watcher-specific profiler options
profiler_group = cfg.OptGroup(
    'profiler',
    title='Profiler Options',
    help='Options for profiling watcher operations using OSProfiler'
)

profiler_opts_list = [
    cfg.BoolOpt(
        'trace_audit_execution',
        default=True,
        help='Enable profiling of audit execution timing. '
             'When enabled, audit picking and execution operations will '
             'be instrumented with osprofiler trace points.'
    ),
    cfg.BoolOpt(
        'trace_memory_usage',
        default=True,
        help='Enable memory usage tracking during audit operations. '
             'When enabled, memory metrics (baseline, peak, delta) will '
             'be captured and attached to profiling traces.'
    ),
]


def register_opts(conf):
    """Register profiler configuration options."""
    profiler_opts.set_defaults(conf)
    conf.register_group(profiler_group)
    conf.register_opts(profiler_opts_list, group=profiler_group)


def list_opts():
    """List profiler configuration options for sample config generation."""
    return {
        profiler_group: profiler_opts_list
    }
