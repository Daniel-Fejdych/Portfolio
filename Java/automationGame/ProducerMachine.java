package automationGame;

public class ProducerMachine extends Machine {
	
    private final Item producedItem;
    private final ItemState producedState;
    private final int baseProductionTime;
    private double progress;
	private final String name;

    public ProducerMachine(String name, Position position, int outputSize,
                            Item producedItem,
                            ItemState producedState,
                            int baseProductionTime,
                            int tier) {

        super(position, 0, outputSize, tier);

        this.producedItem = producedItem;
        this.producedState = producedState;
        this.baseProductionTime = baseProductionTime;
        this.progress = 0;
        this.name = name;
    }

    @Override
    public void tick() {
        // No recipe selection
        progress += speedMultiplier;

        if (progress >= baseProductionTime) {
            progress -= baseProductionTime;

            outputInventory.addItem(
                    producedItem,
                    producedState,
                    1
            );
        }
    }

	@Override
	public double getProgressPercent() {
	    return Math.min(100.0, (progress / baseProductionTime) * 100.0);
	}

	@Override
	public String getName() {
		return producedItem.getName() + name;
	}
	
	@Override
	public int getInputPriority() {
	    return 100;
	}

	@Override
	public int getOutputPriority() {
	    return 0;
	}
}
