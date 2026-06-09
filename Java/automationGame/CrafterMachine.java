package automationGame;

import java.util.List;

public class CrafterMachine extends Machine {
	
    protected final List<Recipe> recipes;
    protected Recipe activeRecipe;
    protected double progress;
    final String name;

    public CrafterMachine(String name, Position position, int inputSize,
            int outputSize, List<Recipe> recipes, int tier) {
        super(position, inputSize, outputSize, tier);
        this.recipes = recipes;
        this.name = name;

    }
       
    public void tick() {
        if (activeRecipe == null) {
            activeRecipe = findCraftableRecipe();
            progress = 0;
        }
        if (activeRecipe != null) {
        	progress += speedMultiplier;

            if (progress >= activeRecipe.getCraftTimeTicks()) {
                completeCraft();
                activeRecipe = null;
            }
        }
    }

    protected Recipe findCraftableRecipe() {
        for (Recipe recipe : recipes) {
            if (canCraft(recipe)) {
                return recipe;
            }
        }
        return null;
    }

    protected boolean canCraft(Recipe recipe) {
        for (Ingredient ingredient : recipe.getInputs()) {
            if (inputInventory.countMatching(ingredient) < ingredient.getAmount()) {
                return false;
            }
        }
        return true;
    }

    protected void consumeInputs(Recipe recipe) {
        for (Ingredient ingredient : recipe.getInputs()) {
            inputInventory.removeMatching(ingredient);
        }
    }

    /**
     * Completes the craft by processing the active recipe.
     */
    protected void completeCraft() {
        // Check if the inputs are still available and can be crafted.
        if (canCraft(activeRecipe)) {

            // Process state transform recipes (one item at a time).
            if (activeRecipe.getStateTransform().isPresent()) {
                StateTransform t = activeRecipe.getStateTransform().get();

                // Find one matching stack in the inventory.
                for (ItemStack stack : inputInventory.getStacks()) {
                    if (stack.getState() == t.getFrom()) {

                        // Add transformed item back as a new stack.
                    	outputInventory.addItem(stack.getItem(), t.getTo(), 1);

                        // Remove the matched input from the inventory.
                        break;
                    }
                }

                // Consume all remaining inputs and return immediately.
                consumeInputs(activeRecipe);
                return;
            }

            // Process normal output recipes.
            for (var entry : activeRecipe.getOutputs().entrySet()) {

                // Add items to the output slots with a quantity of 1.
            	outputInventory.addItem(entry.getKey(), ItemState.INGOT, entry.getValue());
            }

            // Consume all remaining inputs.
            consumeInputs(activeRecipe);
        }
    }

	@Override
	public double getProgressPercent() {		
	    if (activeRecipe == null) return 0;
	    return Math.min(100.0, (progress / activeRecipe.getCraftTimeTicks()) * 100.0);
	}

	@Override
	public String getName() {
		return name;
	}
	
	@Override
	public int getInputPriority() {
	    return 50;
	}

	@Override
	public int getOutputPriority() {
	    return 50;
	}
    
}
