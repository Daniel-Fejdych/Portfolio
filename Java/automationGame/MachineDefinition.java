package automationGame;

import java.util.List;

public class MachineDefinition {
    private final String id;
    private final int inputSize;
    private final int outputSize;
    private final List<Recipe> recipes;

    public MachineDefinition(String id, int inputSize, int outputSize, List<Recipe> recipes) {
        this.id = id;
        this.inputSize = inputSize;
        this.outputSize = outputSize;
        this.recipes = recipes;
    }

    public String getId() {
        return id;
    }

    public int getInputSize() {
        return inputSize;
    }
    public int getOutputSize() {
        return outputSize;
    }

    public List<Recipe> getRecipes() {
        return recipes;
    }
    
    public Machine createInstance(String name, Position pos, int tier) {
        return new CrafterMachine(
        		name,
                pos,
                inputSize,
                outputSize,
                recipes,
                tier
        );
    }
    
    public Machine createInstanceP(String name, Position pos, Item item, ItemState state, int baseProdTime, int tier) {
        return new ProducerMachine(
        		name,
                pos,
                outputSize,
                item,
                state,
                baseProdTime, tier
        );
    
}
}