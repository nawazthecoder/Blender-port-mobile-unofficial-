# Android graphics and texture painting

## Destroyed-mutex error shortly after launch

Revision 15 fixes a duplicate Vulkan submission-completion notification found
after a startup log reported `pthread_mutex_lock called on a destroyed mutex`.
The first notification could let the caller destroy its stack-owned wait state;
the second then tried to lock it. The worker now signals once after cleanup.
The production-code regression fixture and native build/package checks pass.
The user confirms revision 15 fixed this startup failure. The fix remains in
revision 16.

## Shading device loss and a low-memory exit report

Revision 16 targets the remaining Shading failure reported with
`VK_ERROR_DEVICE_LOST` and Android exit reason 3 (`REASON_LOW_MEMORY`). It fixes
texture-pool reuse of incompatible memory type zero, reduces Android allocation
reserves and limits shader compilation to one worker on phones with at most
4 GiB physical RAM. Larger textures and the viewport retain their dimensions.
Native build/package checks and allocator regressions pass; the phone Shading
outcome is still unverified. Install over revision 15 and test the default cube
in Shading first.

If it still closes, reopen once and supply the new startup/previous-session log
and exit report. Revision 16 logs include the APK version and PID, and its exit
report includes recorded process identity and a low-memory flag. A previous log
may describe an older session. PSS/RSS in Android exit reports are last system
samples, not peak memory immediately before death. See
[Android's exit-report reference](https://developer.android.com/reference/android/app/ApplicationExitInfo).

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
