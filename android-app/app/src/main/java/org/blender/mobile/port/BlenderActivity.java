// SPDX-License-Identifier: GPL-2.0-or-later
package org.blender.mobile.port;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.ScaleGestureDetector;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class BlenderActivity extends Activity implements SurfaceHolder.Callback {
    private static final int PICK_BLEND_FILE = 101;
    // Restrict staging on low-storage devices. Larger files need a streaming runtime.
    private static final long MAX_STAGED_BYTES = 256L * 1024L * 1024L;

    static {
        System.loadLibrary("blender_android_bridge");
    }

    private static native String nativeStatus();
    private static native boolean nativeHasRuntime();
    private static native boolean nativeAttachSurface(Surface surface, String cacheDir);
    private static native void nativeResize(int width, int height);
    private static native void nativeDrawFrame();
    private static native void nativeGesture(float dx, float dy, float scale);
    private static native boolean nativeOpenBlend(String absolutePath);
    private static native void nativeDetachSurface();
    private static native void nativeShutdown();

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService fileExecutor = Executors.newSingleThreadExecutor();
    private SurfaceView surfaceView;
    private TextView statusView;
    private ScaleGestureDetector scaleDetector;
    private File stagedBlend;
    private boolean attached = false;
    private boolean resumed = false;
    private boolean destroyed = false;
    private float lastX;
    private float lastY;
    private boolean pointerMoved;

    private final Runnable drawTick = new Runnable() {
        @Override
        public void run() {
            if (!attached || !resumed || destroyed) {
                return;
            }
            nativeDrawFrame();
            // The host runs a deliberately modest preview cadence; the future
            // Blender runtime will own its own native rendering schedule.
            handler.postDelayed(this, 33);
        }
    };

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(25, 27, 32));
        getWindow().setNavigationBarColor(Color.rgb(25, 27, 32));

        int background = Color.rgb(28, 30, 35);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(background);
        setContentView(root);
        // Targeting API 35 uses edge-to-edge on Android 15.
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            int l, t, r, b;
            if (Build.VERSION.SDK_INT >= 30) {
                android.graphics.Insets safe = insets.getInsets(WindowInsets.Type.systemBars());
                l = safe.left;
                t = safe.top;
                r = safe.right;
                b = safe.bottom;
            } else {
                l = insets.getSystemWindowInsetLeft();
                t = insets.getSystemWindowInsetTop();
                r = insets.getSystemWindowInsetRight();
                b = insets.getSystemWindowInsetBottom();
            }
            view.setPadding(l, t, r, b);
            return insets;
        });

        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setPadding(dp(14), dp(8), dp(12), dp(8));
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setBackgroundColor(Color.rgb(41, 43, 49));
        root.addView(toolbar, new LinearLayout.LayoutParams(-1, dp(52)));

        TextView title = new TextView(this);
        title.setText("BLENDER  |  Android port diagnostics");
        title.setTextColor(Color.WHITE);
        title.setTextSize(15);
        toolbar.addView(title, new LinearLayout.LayoutParams(0, -2, 1));

        Button openButton = new Button(this);
        openButton.setText("Open .blend");
        openButton.setAllCaps(false);
        openButton.setOnClickListener(view -> selectBlend());
        toolbar.addView(openButton);

        Button gpuButton = new Button(this);
        gpuButton.setText("GPU info");
        gpuButton.setAllCaps(false);
        gpuButton.setOnClickListener(view -> setStatus(nativeStatus()));
        toolbar.addView(gpuButton);

        FrameLayout viewport = new FrameLayout(this);
        root.addView(viewport, new LinearLayout.LayoutParams(-1, 0, 1));

        surfaceView = new SurfaceView(this);
        surfaceView.getHolder().addCallback(this);
        viewport.addView(surfaceView, new FrameLayout.LayoutParams(-1, -1));

        TextView watermark = new TextView(this);
        watermark.setText("NATIVE GPU DIAGNOSTIC PREVIEW  •  NOT BLENDER'S VIEWPORT");
        watermark.setTextColor(Color.rgb(219, 221, 226));
        watermark.setTextSize(10);
        watermark.setPadding(dp(12), dp(8), dp(12), dp(8));
        watermark.setBackgroundColor(Color.rgb(35, 37, 43));
        FrameLayout.LayoutParams note = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.LEFT);
        note.setMargins(dp(10), dp(10), 0, 0);
        viewport.addView(watermark, note);

        TextView instructions = new TextView(this);
        instructions.setText("Drag to pan diagnostic grid  •  Pinch to zoom");
        instructions.setTextColor(Color.rgb(215, 218, 225));
        instructions.setTextSize(12);
        instructions.setPadding(dp(10), dp(8), dp(10), dp(8));
        FrameLayout.LayoutParams hint = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.LEFT);
        hint.setMargins(dp(10), 0, 0, dp(10));
        viewport.addView(instructions, hint);

        statusView = new TextView(this);
        statusView.setTextSize(12);
        statusView.setTextColor(Color.rgb(234, 235, 238));
        statusView.setPadding(dp(14), dp(7), dp(14), dp(7));
        statusView.setBackgroundColor(Color.rgb(41, 43, 49));
        root.addView(statusView, new LinearLayout.LayoutParams(-1, -2));
        setStatus(nativeStatus());

        scaleDetector = new ScaleGestureDetector(this,
            new ScaleGestureDetector.SimpleOnScaleGestureListener() {
                @Override
                public boolean onScale(ScaleGestureDetector detector) {
                    if (attached) {
                        nativeGesture(0f, 0f, detector.getScaleFactor());
                    }
                    return true;
                }
            });
        surfaceView.setOnTouchListener((view, event) -> {
            scaleDetector.onTouchEvent(event);
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    lastX = event.getX();
                    lastY = event.getY();
                    pointerMoved = false;
                    return true;
                case MotionEvent.ACTION_MOVE:
                    if (event.getPointerCount() == 1 && attached) {
                        float x = event.getX();
                        float y = event.getY();
                        nativeGesture(x - lastX, y - lastY, 1f);
                        lastX = x;
                        lastY = y;
                        pointerMoved = true;
                    }
                    return true;
                case MotionEvent.ACTION_POINTER_UP:
                    // Reset tracking after a pinch to avoid a large jump.
                    lastX = event.getX(0);
                    lastY = event.getY(0);
                    return true;
                case MotionEvent.ACTION_UP:
                    if (!pointerMoved) {
                        view.performClick();
                    }
                    return true;
                default:
                    return true;
            }
        });
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void setStatus(String message) {
        if (statusView != null) {
            statusView.setText(message);
        }
    }

    private void selectBlend() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("*/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        startActivityForResult(intent, PICK_BLEND_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != PICK_BLEND_FILE || resultCode != RESULT_OK || data == null) {
            return;
        }
        Uri uri = data.getData();
        if (uri == null) {
            return;
        }
        setStatus("Copying selected file to private cache. Maximum: 256 MiB.");
        fileExecutor.execute(() -> {
            File next = null;
            try {
                next = File.createTempFile("blender-port-", ".blend", getCacheDir());
                try (InputStream input = getContentResolver().openInputStream(uri);
                     OutputStream output = new FileOutputStream(next)) {
                    if (input == null) {
                        throw new IOException("Document could not be opened");
                    }
                    byte[] buffer = new byte[64 * 1024];
                    long copied = 0;
                    int n;
                    while ((n = input.read(buffer)) != -1) {
                        copied += n;
                        if (copied > MAX_STAGED_BYTES) {
                            throw new IOException("File exceeds 256 MiB staging limit");
                        }
                        output.write(buffer, 0, n);
                    }
                }
                final File selected = next;
                runOnUiThread(() -> {
                    if (destroyed) {
                        selected.delete();
                        return;
                    }
                    if (stagedBlend != null) {
                        stagedBlend.delete();
                    }
                    stagedBlend = selected;
                    if (!nativeHasRuntime()) {
                        setStatus("File staged successfully, but Blender's native runtime is not built yet. This app is a GPU diagnostic host.");
                    } else if (nativeOpenBlend(selected.getAbsolutePath())) {
                        setStatus("File handed to Blender native runtime.");
                    } else {
                        setStatus("Blender runtime could not open this file. Check Android logcat.");
                    }
                });
            } catch (IOException exception) {
                if (next != null) {
                    next.delete();
                }
                final String error = exception.getMessage();
                runOnUiThread(() -> {
                    if (!destroyed) {
                        setStatus("File import failed: " + error);
                    }
                });
            }
        });
    }

    private void attachIfReady() {
        if (attached || !resumed || surfaceView == null) {
            return;
        }
        Surface surface = surfaceView.getHolder().getSurface();
        if (surface == null || !surface.isValid()) {
            return;
        }
        attached = nativeAttachSurface(surface, getCacheDir().getAbsolutePath());
        if (attached) {
            nativeResize(surfaceView.getWidth(), surfaceView.getHeight());
            handler.removeCallbacks(drawTick);
            handler.post(drawTick);
        } else {
            setStatus("Native EGL/Blender surface initialization failed. Inspect logcat.");
        }
    }

    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        attachIfReady();
    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        attachIfReady();
        if (attached) {
            nativeResize(width, height);
        }
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {
        detach();
    }

    private void detach() {
        handler.removeCallbacks(drawTick);
        if (attached) {
            nativeDetachSurface();
            attached = false;
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        resumed = true;
        attachIfReady();
    }

    @Override
    protected void onPause() {
        resumed = false;
        detach();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        destroyed = true;
        detach();
        nativeShutdown();
        fileExecutor.shutdownNow();
        if (stagedBlend != null) {
            stagedBlend.delete();
        }
        super.onDestroy();
    }
}
