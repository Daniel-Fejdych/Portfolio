package automationGame;

public class StateTransform {
    private final ItemState from;
    private final ItemState to;

    public StateTransform(ItemState from, ItemState to) {
        this.from = from;
        this.to = to;
    }

    public ItemState getFrom() {
        return from;
    }

    public ItemState getTo() {
        return to;
    }
}
