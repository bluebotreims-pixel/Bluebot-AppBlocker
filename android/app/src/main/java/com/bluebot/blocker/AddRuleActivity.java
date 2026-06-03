package com.bluebot.blocker;

import android.os.Bundle;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import com.chaquo.python.Python;
import java.util.concurrent.*;
import java.util.regex.Pattern;

public class AddRuleActivity extends AppCompatActivity {

    public static final String PKG = "pkg";
    public static final String NOM = "nom";
    private static final Pattern RE_HORAIRE = Pattern.compile("^([01]\\d|2[0-3]):[0-5]\\d-([01]\\d|2[0-3]):[0-5]\\d$");

    private String pkg, nom;
    private final ExecutorService ex = Executors.newSingleThreadExecutor();

    private Switch swTemps, swLanc, swHor;
    private EditText etTemps, etLanc, etHor;

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_add_rule);

        pkg = getIntent().getStringExtra(PKG);
        nom = getIntent().getStringExtra(NOM);

        ((TextView) findViewById(R.id.tv_titre)).setText("Règles — " + nom);

        swTemps = findViewById(R.id.sw_temps);  etTemps = findViewById(R.id.et_temps);
        swLanc  = findViewById(R.id.sw_lanc);   etLanc  = findViewById(R.id.et_lanc);
        swHor   = findViewById(R.id.sw_hor);    etHor   = findViewById(R.id.et_hor);

        swTemps.setOnCheckedChangeListener((b,on)->etTemps.setEnabled(on));
        swLanc.setOnCheckedChangeListener((b,on)->etLanc.setEnabled(on));
        swHor.setOnCheckedChangeListener((b,on)->etHor.setEnabled(on));

        charger();

        findViewById(R.id.btn_sauvegarder).setOnClickListener(v -> sauvegarder());
        findViewById(R.id.btn_supprimer).setOnClickListener(v -> supprimer());
    }

    private void charger() {
        ex.execute(() -> {
            try {
                com.chaquo.python.PyObject st = Python.getInstance().getModule("storage");
                com.chaquo.python.PyObject reg = st.callAttr("charger_regles");
                com.chaquo.python.PyObject d = reg.get(pkg);
                if (d == null) return;
                for (com.chaquo.python.PyObject r : d.get("regles").asList()) {
                    String type = r.get("type").toString();
                    String val  = r.get("valeur").toString();
                    boolean on  = r.get("active").toBoolean();
                    runOnUiThread(() -> {
                        switch (type) {
                            case "temps":
                                swTemps.setChecked(on); etTemps.setEnabled(on);
                                etTemps.setText(String.valueOf(Integer.parseInt(val) / 60)); break;
                            case "lancements":
                                swLanc.setChecked(on); etLanc.setEnabled(on);
                                etLanc.setText(val); break;
                            case "horaire":
                                swHor.setChecked(on); etHor.setEnabled(on);
                                etHor.setText(val); break;
                        }
                    });
                }
            } catch (Exception e) { android.util.Log.e("BlueBot", e.getMessage()); }
        });
    }

    private void sauvegarder() {
        boolean ok = true;
        if (swTemps.isChecked()) {
            String v = etTemps.getText().toString().trim();
            if (v.isEmpty() || !isPos(v)) { etTemps.setError("Ex: 30 (minutes)"); ok=false; }
            else save("temps", String.valueOf(Integer.parseInt(v)*60));
        }
        if (swLanc.isChecked()) {
            String v = etLanc.getText().toString().trim();
            if (v.isEmpty() || !isPos(v)) { etLanc.setError("Ex: 10"); ok=false; }
            else save("lancements", v);
        }
        if (swHor.isChecked()) {
            String v = etHor.getText().toString().trim();
            if (!RE_HORAIRE.matcher(v).matches()) { etHor.setError("Ex: 22:00-08:00"); ok=false; }
            else save("horaire", v);
        }
        if (ok) { Toast.makeText(this,"✅ Sauvegardé !",Toast.LENGTH_SHORT).show(); finish(); }
    }

    private void save(String type, String val) {
        ex.execute(() -> Python.getInstance().getModule("storage").callAttr("ajouter_regle", pkg, nom, type, val));
    }

    private void supprimer() {
        ex.execute(() -> {
            Python.getInstance().getModule("storage").callAttr("supprimer_regle", pkg);
            runOnUiThread(() -> { Toast.makeText(this,"🗑 Supprimé",Toast.LENGTH_SHORT).show(); finish(); });
        });
    }

    private boolean isPos(String s) { try { return Integer.parseInt(s)>0; } catch(Exception e) { return false; } }

    @Override protected void onDestroy() { super.onDestroy(); ex.shutdown(); }
}
