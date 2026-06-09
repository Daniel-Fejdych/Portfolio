package automationGame;

public class TagStateIngredient implements Ingredient {
    private final String tag;
    private final ItemState requiredState;
    private final int amount;

    public TagStateIngredient(String tag, ItemState requiredState, int amount) {
        this.tag = tag;
        this.requiredState = requiredState;
        this.amount = amount;
    }

    @Override
    public boolean matches(ItemStack stack) {
        return stack.getItem().hasTag(tag)
            && stack.getState() == requiredState;
    }

    @Override
    public int getAmount() {
        return amount;
    }
}
