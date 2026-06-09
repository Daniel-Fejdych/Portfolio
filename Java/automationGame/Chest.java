package automationGame;

public class Chest extends Machine implements InventoryAccess, WorldEntity {

    private final MachineInventory inventory;
    private final Position pos;

    public Chest(Position position, int size) {
    	super(position, size, size, size);
        this.inventory = new MachineInventory(size);
		this.pos = position;
    }

    @Override
    public MachineInventory getInputInventory() {
        return inventory;
    }

    @Override
    public MachineInventory getOutputInventory() {
        return inventory;
    }


	public double getProgressPercent() {
		return -1;
	}

	public String getName() {
		return "Chest";
	}

	@Override
	public Position getPosition() {
		return pos;
	}

	@Override
	public void tick() {}
	
	@Override
	public int getInputPriority() {
	    return 10;
	}

	@Override
	public int getOutputPriority() {
	    return 10;
	}
}