package automationGame;

public class MachineTier {

    private final int level;

    public MachineTier(int level) {
        this.level = level;
    }

    public double getSpeedMultiplier() {
        return Math.pow(2, level - 1);
    }
    public int getTier() {
        return level;
    }
    
}