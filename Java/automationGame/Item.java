package automationGame;

import java.util.Set;

public class Item {
    private final String id;
    private final String name;
    private final int maxStackSize;
    private final Set<String> tags;
    private final Set<ItemState> validStates;

    public Item(String id,
                String name,
                int maxStackSize,
                Set<String> tags,
                Set<ItemState> validStates) {
        this.id = id;
        this.name = name;
        this.maxStackSize = maxStackSize;
        this.tags = tags;
        this.validStates = validStates;
    }

    public String getId() {
        return id;
    }

    public boolean hasTag(String tag) {
        return tags.contains(tag);
    }

    public boolean supportsState(ItemState state) {
        return validStates.contains(state);
    }

    public String getName() {
        return name;
    }

    public int getMaxStackSize() {
        return maxStackSize;
    }

}
