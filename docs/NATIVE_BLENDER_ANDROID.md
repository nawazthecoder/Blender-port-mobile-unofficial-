# Native Blender Android status

The current target is official Blender **5.3.0 stable**, port revision **15**.
See [upgrade details](UPGRADE_5_3.md), the exact [source lock](../config/blender-android.json)
and [build history](PORT_PROGRESS.md). Revision 15 fixes duplicate submission
completion that could access a caller's destroyed wait mutex after startup.
Local regression fixtures pass; the native build and another phone test are
pending. Revision 14's lag improved, but the user's startup crash persisted.
The app package and signing identity are retained.

Use the full native editor workflow, which compiles libblender.so and packages
the real Python/scripts/assets payload. It does not use the historical diagnostic
launcher scaffold in android-app/. APK audits, signature and matching-update-key
checks must pass before release. Passing those checks does not establish that
every feature works on a phone.

The package is org.blender.androidport. VersionCode 5030015 updates the existing
app when signed with the retained certificate. Save projects before updating.
