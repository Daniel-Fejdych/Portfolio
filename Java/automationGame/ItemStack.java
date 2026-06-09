package automationGame;

public class ItemStack {
    private final Item item;
    private ItemState state;
    private int quantity;

    public ItemStack(Item item, ItemState state, int quantity) {
        if (!item.supportsState(state)) {
            throw new IllegalArgumentException("Invalid state for item");
        }
        this.item = item;
        this.state = state;
        this.quantity = quantity;
    }

    public Item getItem() {
        return item;
    }

    public ItemState getState() {
        return state;
    }

    public void setState(ItemState newState) {
        if (!item.supportsState(newState)) {
            throw new IllegalArgumentException("Invalid state for item");
        }
        this.state = newState;
    }

    public int getQuantity() {
        return quantity;
    }

    public void remove(int amount) {
        quantity -= amount;
    }

    public void add(int amount) {
        quantity += amount;
    }
    


}
