package automationGame;


import java.util.List;
import java.util.Map;
import java.util.Optional;

public class Recipe {
    private final List<Ingredient> inputs;
    private final Map<Item, Integer> outputs;
    private final Optional<StateTransform> stateTransform;
    private final int craftTimeTicks;

    public Recipe(List<Ingredient> inputs,
                  Map<Item, Integer> outputs,
                  StateTransform stateTransform,
                  int craftTimeTicks) {
        this.inputs = inputs;
        this.outputs = outputs;
        this.stateTransform = Optional.ofNullable(stateTransform);
        this.craftTimeTicks = craftTimeTicks;
    }

    public Optional<StateTransform> getStateTransform() {
        return stateTransform;
    }

    public List<Ingredient> getInputs() {
        return inputs;
    }

    public Map<Item, Integer> getOutputs() {
        return outputs;
    }

    public int getCraftTimeTicks() {
        return craftTimeTicks;
    }
}