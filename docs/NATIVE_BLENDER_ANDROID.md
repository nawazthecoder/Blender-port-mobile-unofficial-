# Native Blender Android status

The current target is official Blender **5.3.0 stable**, port revision **14**.
See [upgrade details](UPGRADE_5_3.md), the exact [source lock](../config/blender-android.json)
and [build history](PORT_PROGRESS.md). Full native compilation and APK validation
passed in [workflow 43455837164](https://github.com/nawazthecoder/Blender-port-mobile-unofficial-/actions/runs/43455837164).
That revision 13 APK is reported to lag and crash on the phone. Revision 14
fixes a confirmed framebuffer-retirement gap; its new native build is pending.
The package and signing certificate are retained. The
previous validated 5.2.3 Android revision 12 remains recorded as a fallback.

Use the full native editor workflow, which compiles libblender.so and packages
the real Python/scripts/assets payload. It does not use the historical diagnostic
launcher scaffold in android-app/. APK audits, signature and matching-update-key
checks must pass before release. Passing those checks does not establish that
every feature works on a phone.

The package is org.blender.androidport. VersionCode 5030014 updates the existing
app when signed with the retained certificate. Save projects before updating.
