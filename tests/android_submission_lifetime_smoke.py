#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compile the production submission caller and worker tail with mocked GPU calls.

A controlled resource-release gate verifies that a stack-owned waiter cannot
return before worker cleanup. The negative control restores the duplicate early
notification and must fail before the worker can touch the expired waiter again.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile


def definition(text, marker, semicolon=False):
    start = text.index(marker)
    end = text.index('{', start) + 1
    depth = 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end] + (';' if semicolon else '')


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--vulkan-include', required=True, type=Path)
parser.add_argument('--negative-control', action='store_true')
args = parser.parse_args()
source = (args.source / 'source/blender/gpu/vulkan/vk_device_submission.cc').read_text()
runner = definition(source, 'void VKDevice::submission_runner(')
start = runner.index('    if (submit_task->submit_to_device) {')
marker = '    MEM_delete<VKRenderGraphSubmitTask>(submit_task);'
end = runner.index(marker, start) + len(marker)
worker = runner[start:end]
if args.negative_control:
    early = '''      if (submit_task->wait_for_submission != nullptr) {
        std::unique_lock<Mutex> lock(submit_task->wait_for_submission->is_submitted_mutex);
        submit_task->wait_for_submission->is_submitted = true;
        submit_task->wait_for_submission->is_submitted_condition.notify_one();
      }
'''
    insertion = '      command_buffers_in_use.append_timeline('
    assert worker.count(insertion) == 1
    worker = worker.replace(insertion, early + insertion)
parts = {
    'WAIT_TYPE': definition(source, 'struct VKRenderGraphWait {', True),
    'TASK_TYPE': definition(source, 'struct VKRenderGraphSubmitTask {', True),
    'CALLER': definition(source, 'TimelineValue VKDevice::render_graph_submit('),
    'WORKER': worker,
}
fixture = Path(__file__).with_suffix('.cc.in').read_text()
for name, text in parts.items():
    fixture = fixture.replace('@' + name + '@', text)
with tempfile.TemporaryDirectory(prefix='android-submission-lifetime-') as directory:
    cpp = Path(directory) / 'submission.cc'
    binary = Path(directory) / 'submission'
    cpp.write_text(fixture)
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++20', '-Wall', '-Wextra', '-Werror',
                    '-pthread', '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-g',
                    '-I', str(args.vulkan_include.resolve()), str(cpp), '-o', str(binary)],
                   check=True)
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
    if args.negative_control:
        assert result.returncode != 0 and 'completion_precedes_cleanup' in result.stderr, result.stderr
        print('Negative control rejected: caller returned before cleanup and waiter lifetime ended')
    else:
        if result.returncode:
            raise RuntimeError(result.stderr)
        print(result.stdout.strip())
