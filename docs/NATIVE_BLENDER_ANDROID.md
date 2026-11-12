# Native Blender Android status

The current target is official Blender **5.3.0 stable**, port revision **13**.
See [upgrade details](UPGRADE_5_3.md), the exact [source lock](../config/blender-android.json)
and [build history](PORT_PROGRESS.md). This source migration is awaiting native
compilation and device verification. The prior validated package is Blender
5.2.3 Android revision 12.

Use the full native editor workflow, which compiles libblender.so and packages
the real Python/scripts/assets payload. It does not use the historical diagnostic
launcher scaffold in android-app/. APK audits, signature and matching-update-key
checks must pass before release. Passing those checks does not establish that
every feature works on a phone.

The package is org.blender.androidport. VersionCode 5030013 updates the existing
app when signed with the retained certificate. Save projects before updating.
