# Android virtual mouse (revision 9)

Install the new **Blender Android** app. It uses package `org.blender.androidport`
so it can sit alongside the working revision 7 **Blender** app. Save your work in
shared storage before testing and open those files in the new app. Settings and
app-private files belong to each app separately. Do not uninstall the working app
just to try this build. The Java activity retains its original fully qualified
class name for native JNI compatibility.

Tap **MOUSE** beside **KEYBOARD** on the bottom status bar. If the status bar is
hidden, use operator search (F3) and choose **Toggle Virtual Mouse**.

- Swipe outside the controls to move the arrow; lifting your finger keeps its position.
- Tap **Left**, **Middle**, or **Right** to click at the arrow tip. A short tap on
  the touchpad also clicks the left button. Swiping does not click.
- For a one-finger drag, tap **Hold**, then a mouse button. It stays held while
  you swipe. Tap **Release**, or that same button, to finish. Holding Middle lets
  you orbit the viewport; a latched Shift key on the virtual keyboard adds pan.
- You can also keep a finger on a mouse button and move another finger to drag.
- Use **Wheel - / Wheel +**, or move two fingers vertically together, to scroll
  or zoom at the pointer. The existing touch orbit/pinch gestures are replaced
  while mouse mode is active.
- Drag **Move** to reposition the control strip. The strip avoids the open
  virtual keyboard, whose keys still respond to direct touches. While the keyboard
  is open, the pointer stays in the visible editor area so drag releases cannot
  be swallowed by a key.
- Tap **Close** or **MOUSE** to return to direct touch. A physical mouse or stylus
  switches off virtual mouse mode automatically and keeps its existing input behavior.

Held buttons are released on cancel, app focus loss, surface loss, rotation, and
when mouse mode closes. Closing the strip consumes the remainder of that touch
so it cannot click the Blender editor underneath.

## Validation

The real controller is exercised by `tests/android_virtual_mouse_smoke.py` with
AddressSanitizer and UndefinedBehaviorSanitizer. Tests cover click coordinates,
relative motion, latched left/middle/right drags, reordered touch IDs, two-finger
scrolling, keyboard exclusion, moving the strip, and releasing interrupted input.
Full native compilation, APK identity, signatures, ELF dependency closure and
runtime payload checks run in GitHub Actions. Phone validation of this new mode
remains pending; revision 7 startup was confirmed separately by the user.

The CI development signing key is cached under `android-port-development-signing-v1`
so later builds can update this new app while that cache is retained. It is a
public development identity, not a production signing secret. Revision 7 was
signed with a different ephemeral key; its private key was not preserved, which
is why this build uses a separate application ID.
