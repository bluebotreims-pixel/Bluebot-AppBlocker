package com.bluebot.blocker;

public class RuleItem {
    public final String packageName, nom, progression;
    public final boolean bloquee;
    public RuleItem(String p, String n, String prog, boolean b) {
        packageName = p; nom = n; progression = prog; bloquee = b;
    }
}
