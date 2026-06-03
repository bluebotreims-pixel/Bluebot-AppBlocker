package com.bluebot.blocker;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Service d'accessibilité — détecte l'app en premier plan
 * et demande au moteur Python si elle doit être bloquée.
 */
public class BlockerService extends AccessibilityService {

    private static final String TAG = "BlueBot";
    private ExecutorService executor;
    private PyObject rulesEngine;
    private PyObject storage;

    private String dernierPkg = "";
    private long dernierTemps = 0;
    private static final long COOLDOWN = 20_000L;

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        executor = Executors.newSingleThreadExecutor();
        Python py = Python.getInstance();
        rulesEngine = py.getModule("rules_engine");
        storage = py.getModule("storage");
        Log.i(TAG, "Service connecté");
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null || event.getEventType() != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return;
        CharSequence pkg = event.getPackageName();
        if (pkg == null) return;
        String p = pkg.toString();
        if (p.equals(getPackageName()) || p.startsWith("com.android.") || p.equals("android")) return;

        executor.execute(() -> {
            try {
                storage.callAttr("enregistrer_ouverture", p);
                PyObject dec = rulesEngine.callAttr("verifier", p);
                if (dec.get("bloquer").toBoolean()) {
                    long now = System.currentTimeMillis();
                    if (!p.equals(dernierPkg) || now - dernierTemps > COOLDOWN) {
                        dernierPkg = p;
                        dernierTemps = now;
                        String msg = dec.get("message").toString();
                        Intent i = new Intent(getApplicationContext(), WarningActivity.class);
                        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                        i.putExtra(WarningActivity.CLE_MESSAGE, msg);
                        getApplicationContext().startActivity(i);
                    }
                }
            } catch (Exception e) {
                Log.e(TAG, e.getMessage());
            }
        });
    }

    @Override public void onInterrupt() {}

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (executor != null) executor.shutdown();
    }
}
