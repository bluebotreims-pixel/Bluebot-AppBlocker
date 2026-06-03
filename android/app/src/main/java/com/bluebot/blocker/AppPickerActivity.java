package com.bluebot.blocker;

import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.*;
import android.widget.*;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.*;
import java.util.*;
import java.util.concurrent.*;

public class AppPickerActivity extends AppCompatActivity {

    private Adapter adapter;
    private List<AppInfo> tous = new ArrayList<>();
    private final ExecutorService ex = Executors.newSingleThreadExecutor();

    @Override
    protected void onCreate(Bundle s) {
        super.onCreate(s);
        setContentView(R.layout.activity_app_picker);

        RecyclerView rv = findViewById(R.id.rv_apps);
        adapter = new Adapter(app -> {
            Intent i = new Intent(this, AddRuleActivity.class);
            i.putExtra(AddRuleActivity.PKG, app.pkg);
            i.putExtra(AddRuleActivity.NOM, app.nom);
            startActivity(i);
        });
        rv.setLayoutManager(new LinearLayoutManager(this));
        rv.setAdapter(adapter);

        EditText et = findViewById(R.id.et_recherche);
        et.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s2, int a, int b, int c) {}
            @Override public void onTextChanged(CharSequence s2, int a, int b, int c) { filtrer(s2.toString()); }
            @Override public void afterTextChanged(Editable s2) {}
        });

        ex.execute(this::charger);
    }

    private void charger() {
        PackageManager pm = getPackageManager();
        Intent intent = new Intent(Intent.ACTION_MAIN);
        intent.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> list = pm.queryIntentActivities(intent, 0);
        List<AppInfo> apps = new ArrayList<>();
        for (ResolveInfo r : list) {
            String pkg = r.activityInfo.packageName;
            if (pkg.equals(getPackageName())) continue;
            String nom;
            try { nom = pm.getApplicationLabel(pm.getApplicationInfo(pkg, 0)).toString(); }
            catch (PackageManager.NameNotFoundException e) { nom = pkg; }
            apps.add(new AppInfo(pkg, nom));
        }
        Collections.sort(apps, (a, b) -> a.nom.compareToIgnoreCase(b.nom));
        tous = apps;
        runOnUiThread(() -> adapter.setListe(apps));
    }

    private void filtrer(String q) {
        if (q.isEmpty()) { adapter.setListe(tous); return; }
        String lq = q.toLowerCase();
        List<AppInfo> f = new ArrayList<>();
        for (AppInfo a : tous) if (a.nom.toLowerCase().contains(lq) || a.pkg.toLowerCase().contains(lq)) f.add(a);
        adapter.setListe(f);
    }

    @Override protected void onDestroy() { super.onDestroy(); ex.shutdown(); }

    static class AppInfo { final String pkg, nom; AppInfo(String p, String n) { pkg=p; nom=n; } }

    static class Adapter extends RecyclerView.Adapter<Adapter.VH> {
        interface Sel { void sel(AppInfo a); }
        private List<AppInfo> liste = new ArrayList<>();
        private final Sel s;
        Adapter(Sel s) { this.s = s; }
        void setListe(List<AppInfo> l) { this.liste = l; notifyDataSetChanged(); }
        @NonNull @Override public VH onCreateViewHolder(@NonNull ViewGroup p, int t) {
            return new VH(LayoutInflater.from(p.getContext()).inflate(R.layout.item_app, p, false));
        }
        @Override public void onBindViewHolder(@NonNull VH h, int i) { h.bind(liste.get(i)); }
        @Override public int getItemCount() { return liste.size(); }
        class VH extends RecyclerView.ViewHolder {
            TextView tvN, tvP;
            VH(View v) { super(v); tvN=v.findViewById(R.id.tv_nom_app); tvP=v.findViewById(R.id.tv_package); v.setOnClickListener(x->s.sel(liste.get(getAdapterPosition()))); }
            void bind(AppInfo a) { tvN.setText(a.nom); tvP.setText(a.pkg); }
        }
    }
}
