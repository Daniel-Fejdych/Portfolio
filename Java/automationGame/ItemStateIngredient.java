package automationGame;

public class ItemStateIngredient implements Ingredient {
    private final Item item;
    private final ItemState requiredState;
    private final int amount;

    public ItemStateIngredient(Item item, ItemState requiredState, int amount) {
        this.item = item;
        this.requiredState = requiredState;
        this.amount = amount;
    }

    @Override
    public boolean matches(ItemStack stack) {
        return stack.getItem().getId().equals(item.getId())
                && stack.getState() == requiredState;
    }

    @Override
    public int getAmount() {
        return amount;
    }

    public Item getItem() {
        return item;
    }
}

