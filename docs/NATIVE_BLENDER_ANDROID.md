# Native Blender Android status

The current target is official Blender **5.3.0 stable**, port revision **16**.
See [upgrade details](UPGRADE_5_3.md), the exact [source lock](../config/blender-android.json)
and [build history](PORT_PROGRESS.md). The user confirms revision 15 fixed the
destroyed-mutex startup crash; entering Shading still fails. Its new log reports
Vulkan device loss and its exit report records a low-memory kill.
Revision 16 corrects texture-pool memory-type compatibility and reduces Android
allocation reserves and compiler concurrency. Regression fixtures and full
native build/package/signature checks pass in
[workflow 43699738130](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/43699738130).
The downloaded APK and corresponding source were verified. A phone Shading
retest is pending. The app package and signing identity are retained.

Use the full native editor workflow, which compiles libblender.so and packages
the real Python/scripts/assets payload. It does not use the historical diagnostic
launcher scaffold in android-app/. APK audits, signature and matching-update-key
checks must pass before release. Passing those checks does not establish that
every feature works on a phone.

The package is org.blender.androidport. VersionCode 5030016 updates the existing
app when signed with the retained certificate. Save projects before updating.
