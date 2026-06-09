package automationGame;

public interface InventoryAccess {
    MachineInventory getInputInventory();
    MachineInventory getOutputInventory();
    
    default int getInputPriority() {
        return 0;
    }

    default int getOutputPriority() {
        return 0;
    }
}
