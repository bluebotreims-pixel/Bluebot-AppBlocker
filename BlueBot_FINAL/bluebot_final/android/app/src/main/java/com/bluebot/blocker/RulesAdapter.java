package com.bluebot.blocker;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.Switch;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.ArrayList;
import java.util.List;

public class RulesAdapter extends RecyclerView.Adapter<RulesAdapter.VH> {

    public interface OnDel    { void del(String pkg); }
    public interface OnToggle { void toggle(String pkg, boolean on); }

    private List<RuleItem> liste = new ArrayList<>();
    private final OnDel onDel;
    private final OnToggle onToggle;

    public RulesAdapter(OnDel onDel, OnToggle onToggle) { this.onDel = onDel; this.onToggle = onToggle; }

    public void setListe(List<RuleItem> l) { this.liste = l; notifyDataSetChanged(); }

    @NonNull @Override
    public VH onCreateViewHolder(@NonNull ViewGroup p, int t) {
        return new VH(LayoutInflater.from(p.getContext()).inflate(R.layout.item_regle, p, false));
    }

    @Override public void onBindViewHolder(@NonNull VH h, int i) { h.bind(liste.get(i)); }
    @Override public int getItemCount() { return liste.size(); }

    class VH extends RecyclerView.ViewHolder {
        TextView tvNom, tvPkg, tvProg, tvStatut;
        Switch sw;
        ImageButton btnDel;

        VH(View v) {
            super(v);
            tvNom    = v.findViewById(R.id.tv_nom_app);
            tvPkg    = v.findViewById(R.id.tv_package);
            tvProg   = v.findViewById(R.id.tv_progression);
            tvStatut = v.findViewById(R.id.tv_statut);
            sw       = v.findViewById(R.id.switch_actif);
            btnDel   = v.findViewById(R.id.btn_supprimer);
        }

        void bind(RuleItem item) {
            tvNom.setText(item.nom);
            tvPkg.setText(item.packageName);
            tvProg.setText(item.progression);
            if (item.bloquee) {
                tvStatut.setText("🔴 BLOQUÉE");
                tvStatut.setTextColor(itemView.getContext().getColor(R.color.rouge));
            } else {
                tvStatut.setText("🟢 Active");
                tvStatut.setTextColor(itemView.getContext().getColor(R.color.vert));
            }
            sw.setOnCheckedChangeListener(null);
            sw.setChecked(!item.bloquee);
            sw.setOnCheckedChangeListener((b, on) -> onToggle.toggle(item.packageName, on));
            btnDel.setOnClickListener(v -> onDel.del(item.packageName));
        }
    }
}
