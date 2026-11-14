# SPDX-License-Identifier: GPL-2.0-or-later
"""Run inside the Android Blender Python console/Text Editor after installation.
Creates a temporary scene, saves/reopens it and renders a small CPU Cycles image.
Uses a separate .blend under the app temp directory. Save your work first:
this intentionally replaces the open scene. Failure raises, never prints PASS.
"""
import bpy
import json
from pathlib import Path
import tempfile

assert bpy.app.version[:3] == (5, 3, 0), bpy.app.version_string
assert bpy.app.build_options.cycles
assert bpy.app.build_options.fluid
assert bpy.app.build_options.alembic
assert bpy.app.build_options.usd
out = Path(tempfile.mkdtemp(prefix='blender-android-smoke-', dir=bpy.app.tempdir))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.object
obj.name = 'AndroidSmokeCube'
obj.modifiers.new('Subdivision', 'SUBSURF').levels = 1
bpy.ops.object.camera_add(location=(4, -4, 3))
camera = bpy.context.object
camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = camera
bpy.ops.object.light_add(type='AREA', location=(2, -2, 4))
bpy.context.object.data.energy = 600
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 4
scene.render.resolution_x = scene.render.resolution_y = 64
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(out / 'cycles.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'smoke.blend'))
bpy.ops.wm.open_mainfile(filepath=str(out / 'smoke.blend'))
assert 'AndroidSmokeCube' in bpy.data.objects
bpy.ops.render.render(write_still=True)
assert (out / 'cycles.png').stat().st_size > 0
result = {'version': bpy.app.version_string, 'save_reload': True, 'cycles_cpu_render': True,
          'device_ui_lifecycle': 'manual verification required', 'directory': str(out)}
(out / 'result.json').write_text(json.dumps(result, indent=2))
print('ANDROID RUNTIME SMOKE PASS', result)
