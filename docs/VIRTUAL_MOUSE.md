# Android virtual mouse (revision 10)

Install revision 10 over **Blender Android** revision 9. It keeps the same
`org.blender.androidport` application ID and the CI development signing identity.
The separate revision 7 **Blender** app can remain installed. Save your work before
updating; uninstalling the app is not part of the update procedure.

Tap **MOUSE** beside **KEYBOARD** on the bottom status bar. If the status bar is
hidden, use operator search (F3) and choose **Toggle Virtual Mouse**.

| Gesture in mouse mode | Action |
| --- | --- |
| One-finger swipe | Move the pointer; lifting leaves it in place |
| Single short tap | Left click at the pointer |
| Two quick taps with one finger | Right click, without a preceding left click |
| Two-finger quick tap | Right click as an alternative |
| Two fingers held or dragged together | Hold Middle and move; lift a finger to release |
| Three fingers moved vertically | Wheel scrolling / zooming in either direction |

Pad taps briefly wait up to 240 ms to distinguish a single tap from a double tap.
Movement has no recognition delay or smoothing filter. The **Left / Middle /
Right** buttons click immediately, including when double-clicking with Left.

For one-finger dragging, tap **Hold**, then a mouse button. It stays held while
you swipe. Tap **Release**, or the same button, to finish. You can also keep one
finger on a button and move another finger. Explicit held buttons take priority
over the automatic gestures. A latched Shift key on the virtual keyboard plus
Middle pans the viewport. **Wheel - / Wheel +** remain available.

The two-finger hold starts after 180 ms, or immediately when a drag moves past
touch slop. Adding a third finger releases Middle before scrolling. After any
finger in a multi-finger gesture lifts, the remaining fingers cannot accidentally
start another drag or click; lift them all to begin the next gesture.

Drag **Move** to reposition the control strip. It avoids the open virtual keyboard,
whose keys still respond to direct touches. The pointer stays in the visible
editor area while the keyboard is open so keys cannot swallow a drag release.
Tap **Close** to return to direct touch. A physical mouse or stylus automatically
switches off virtual mouse mode.

Held buttons and pending taps are cancelled on focus loss, surface loss, rotation,
cancellation, and when mouse mode closes. Closing the strip consumes the rest of
that touch stream to prevent click-through.

## Visibility and responsiveness

The pointer is now drawn after floating menus, gestures, drag previews and Blender's
software cursor. Opening an options menu no longer places it over the arrow.
The control strip remains in its normal window overlay layer.

Virtual touch movement no longer posts full-window `NC_WINDOW` refresh requests.
Only the window composition is marked dirty when pointer or control state changes;
existing region buffers can be reused. Idle state does not request redraws.
Hover events are collapsed to the newest position before each Blender iteration,
with button/wheel boundaries flushed in order. Every movement sample is retained
while a mouse button is held, preserving paint strokes and drags. This addresses
unnecessary redraw work and stale hover backlogs; phone FPS and latency still need
measurement on the user's device.

## Validation

`tests/android_virtual_mouse_smoke.py` runs the actual controller and event queue
with AddressSanitizer and UndefinedBehaviorSanitizer. Coverage includes click
timing and coordinates, double-tap suppression of Left, two-finger Middle holds
and drags, three-finger scrolling both ways, gesture transitions, interrupted
input, keyboard exclusion, toolbar controls, a 10,000-event hover burst, ordered
button/wheel events, and preserved held-button movement samples.

Revision 9 passed native compilation, package identity, dependency/payload audits
and v3 signature checks in [workflow 41582692540](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41582692540).
The user reports using it on their phone and identified menu occlusion and pointer
lag. Revision 10 passed full native build, package identity, runtime/ELF/dependency
audits and v3 signature validation in [workflow 41589347500](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/41589347500).
Its signing certificate matches revision 9, allowing an update over that app.
Phone verification of revision 10 and measured latency remain pending.

The CI development key is cached under `android-port-development-signing-v1`;
future update compatibility depends on retaining this key. The Java activity's
fully qualified original class name is preserved for JNI compatibility.
