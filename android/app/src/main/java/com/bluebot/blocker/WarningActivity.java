package com.bluebot.blocker;

import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class WarningActivity extends AppCompatActivity {

    public static final String CLE_MESSAGE = "message";
    private CountDownTimer timer;
    private TextView tvCompteur;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(
            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED |
            WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON  |
            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
        );
        setContentView(R.layout.activity_warning);

        TextView tvMsg = findViewById(R.id.tv_message);
        tvCompteur = findViewById(R.id.tv_compteur);
        Button btnRetour = findViewById(R.id.btn_retour);

        String msg = getIntent().getStringExtra(CLE_MESSAGE);
        tvMsg.setText(msg != null ? msg : "⛔  Limite atteinte !\n\nL'application va être fermée.");

        btnRetour.setOnClickListener(v -> retourAccueil());
        vibrer();
        demarrerCompteur();
    }

    private void demarrerCompteur() {
        timer = new CountDownTimer(10_000, 1_000) {
            @Override
            public void onTick(long ms) {
                long s = ms / 1000 + 1;
                tvCompteur.setText(String.valueOf(s));
                if (s <= 3)      tvCompteur.setTextColor(getColor(R.color.rouge));
                else if (s <= 6) tvCompteur.setTextColor(getColor(R.color.orange));
                else             tvCompteur.setTextColor(getColor(R.color.blanc));
            }
            @Override public void onFinish() { retourAccueil(); }
        }.start();
    }

    private void retourAccueil() {
        if (timer != null) timer.cancel();
        Intent i = new Intent(Intent.ACTION_MAIN);
        i.addCategory(Intent.CATEGORY_HOME);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(i);
        finish();
    }

    private void vibrer() {
        try {
            Vibrator v = (Vibrator) getSystemService(VIBRATOR_SERVICE);
            if (v == null) return;
            long[] pattern = {0, 400, 200, 400};
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                v.vibrate(VibrationEffect.createWaveform(pattern, -1));
            else v.vibrate(pattern, -1);
        } catch (Exception ignored) {}
    }

    @Override public void onBackPressed() { retourAccueil(); }
    @Override protected void onDestroy() { if (timer != null) timer.cancel(); super.onDestroy(); }
}
