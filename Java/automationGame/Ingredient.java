package automationGame;

public interface Ingredient {
    boolean matches(ItemStack stack);
    int getAmount();
}