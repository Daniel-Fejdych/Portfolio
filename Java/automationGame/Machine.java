package automationGame;

public abstract class Machine implements WorldEntity, InventoryAccess{
	
    protected final Position position;

    protected final MachineInventory inputInventory;
    protected final MachineInventory outputInventory;
    
    protected final MachineTier tier;
    protected final double speedMultiplier;


    public Machine(Position position, int inputSize,
            int outputSize, int tier) {       
    	this.position = position;
        this.inputInventory = new MachineInventory(inputSize);
        this.outputInventory = new MachineInventory(outputSize);
        this.tier = new MachineTier(tier);
        this.speedMultiplier = this.tier.getSpeedMultiplier();
    }
    
    public int getTier() {
        return tier.getTier();
    }

    @Override
    public MachineInventory getInputInventory() {
        return inputInventory;
    }

    @Override
    public MachineInventory getOutputInventory() {
        return outputInventory;
    }

    abstract public void tick();
    
    public Position getPosition(){
    	return position;
    }
    
    public abstract double getProgressPercent();

    public abstract String getName();
    
    
    

}
