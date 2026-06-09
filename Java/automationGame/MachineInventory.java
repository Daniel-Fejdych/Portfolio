package automationGame;

public class MachineInventory extends Inventory {

    public MachineInventory(int capacity) {
        super(capacity);
    }

    public boolean canAccept(Item item) {
        return true; // later: filters, IO rules
    }

}
