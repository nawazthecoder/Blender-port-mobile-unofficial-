# Android graphics and texture painting

## A Vulkan/OpenGL fallback message while Blender is drawing

Revision 7 compiles only the Vulkan display backend. A working viewport in that
APK cannot be an OpenGL fallback.

The desktop factory preference selects OpenGL. The Android build rejects that
unavailable preference, selects Vulkan, and sets the shared fallback flag. The
desktop popup incorrectly assumes every fallback goes from Vulkan to OpenGL.

For the installed revision 7 build, select **Edit > Preferences > System >
Display Graphics > Backend > Vulkan**, save preferences, and restart Blender.
This changes the stored preference; it does not bypass device capability checks.

Revision 8 normalizes unsupported desktop backend preferences to Vulkan on
Android. An explicitly requested launch override keeps its priority. If a
fallback is still required, the Android popup names the backend actually in use.

If a graphics problem remains, the native Python Console can report the active
backend and renderer without changing the scene:

```python
import gpu
print(gpu.platform.backend_type_get(), gpu.platform.renderer_get(), gpu.platform.version_get())
```

The app also writes `blender-startup.log`; a startup toast shows its location.
After granting all-files access and restarting, Downloads is the first location
it tries. Keep a fresh log for the exact APK revision being tested.

## Purple objects and missing textures in Texture Paint

On a fresh mesh, this usually means no image has been selected as the paint
canvas. The warning can also refer to a missing image file or linked/read-only
data. It is separate from graphics backend selection.

For a fresh cube:

1. Open Texture Paint and select the cube.
2. Open **Texture Slots** in the 3D Viewport header and press **+**.
3. Choose **Base Color**. Give the image a name, use 512 x 512 for a small test,
   choose a white fill, and press **Add**.
4. If **Add Simple UVs** is offered, use it. The factory cube already has UVs.
5. Select the new slot and a paint brush, then paint.
6. Use **Save All Images** to save the edited image as well as the `.blend` file.

For an imported model, first check whether its existing image files are present
and accessible; reconnect those images rather than replacing them with a blank
canvas. If a valid, selected image remains purple, capture the Texture Slots
panel and the current startup log for further diagnosis.

Reference: [Blender Texture Slots manual](https://docs.blender.org/manual/en/latest/sculpt_paint/texture_paint/tool_settings/texture_slots.html).
