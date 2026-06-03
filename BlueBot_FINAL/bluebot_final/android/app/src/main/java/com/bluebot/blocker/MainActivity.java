package com.bluebot.blocker;

import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.google.android.material.floatingactionbutton.FloatingActionButton;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {

    private CardView cardStatut;
    private TextView tvStatut;
    private Button btnActiver;
    private TextView tvVide;
    private RulesAdapter adapter;
    private final ExecutorService ex = Executors.newSingleThreadExecutor();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        cardStatut = findViewById(R.id.card_statut);
        tvStatut   = findViewById(R.id.tv_statut);
        btnActiver = findViewById(R.id.btn_activer);
        tvVide     = findViewById(R.id.tv_vide);

        RecyclerView rv = findViewById(R.id.rv_regles);
        adapter = new RulesAdapter(
            pkg -> supprimerRegle(pkg),
            (pkg, on) -> togglerRegle(pkg, on)
        );
        rv.setLayoutManager(new LinearLayoutManager(this));
        rv.setAdapter(adapter);

        btnActiver.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));

        FloatingActionButton fab = findViewById(R.id.fab);
        fab.setOnClickListener(v -> startActivity(new Intent(this, AppPickerActivity.class)));
    }

    @Override
    protected void onResume() {
        super.onResume();
        verifierService();
        chargerRegles();
    }

    private void verifierService() {
        String s = getPackageName() + "/" + BlockerService.class.getCanonicalName();
        String actifs = Settings.Secure.getString(getContentResolver(), Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        boolean ok = actifs != null && actifs.contains(s);
        cardStatut.setCardBackgroundColor(getColor(ok ? R.color.vert : R.color.rouge));
        tvStatut.setText(ok ? "✅  Service actif — surveillance en cours" : "⚠️  Service inactif — appuyez pour activer");
        btnActiver.setVisibility(ok ? View.GONE : View.VISIBLE);
    }

    private void chargerRegles() {
        ex.execute(() -> {
            List<RuleItem> items = new ArrayList<>();
            try {
                Python py = Python.getInstance();
                PyObject storage = py.getModule("storage");
                PyObject engine  = py.getModule("rules_engine");
                PyObject regles  = storage.callAttr("charger_regles");
                for (Map.Entry<PyObject, PyObject> e : regles.asMap().entrySet()) {
                    String pkg  = e.getKey().toString();
                    String nom  = e.getValue().get("nom").toString();
                    PyObject pr = engine.callAttr("progression", pkg);
                    boolean bl  = engine.callAttr("verifier", pkg).get("bloquer").toBoolean();
                    items.add(new RuleItem(pkg, nom, pr != null ? pr.toString() : "—", bl));
                }
            } catch (Exception e) { Log.e("BlueBot", e.getMessage()); }
            List<RuleItem> fi = items;
            runOnUiThread(() -> {
                adapter.setListe(fi);
                tvVide.setVisibility(fi.isEmpty() ? View.VISIBLE : View.GONE);
            });
        });
    }

    private void supprimerRegle(String pkg) {
        ex.execute(() -> {
            Python.getInstance().getModule("storage").callAttr("supprimer_regle", pkg);
            runOnUiThread(this::chargerRegles);
        });
    }

    private void togglerRegle(String pkg, boolean on) {
        ex.execute(() -> Python.getInstance().getModule("storage").callAttr("toggler_regles", pkg, on));
    }

    @Override protected void onDestroy() { super.onDestroy(); ex.shutdown(); }
}
