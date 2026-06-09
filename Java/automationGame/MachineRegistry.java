package automationGame;

import java.util.HashMap;
import java.util.Map;

public class MachineRegistry {


    public static MachineDefinition get(String id) {
        return DEFINITIONS.get(id);
    }

    private static final Map<String, MachineDefinition> DEFINITIONS = new HashMap<>();

    public static void register(MachineDefinition def) {
        DEFINITIONS.put(def.getId(), def);
    }

    public static Machine create(String name, Position pos, int tier) {
        MachineDefinition def = DEFINITIONS.get(name);
        if (def == null) {
            throw new IllegalArgumentException("Unknown machine: " + name);
        }
        return def.createInstance(name, pos, tier);
    }
    
    public static Machine createP(String name, Position pos, Item item, ItemState state, int baseProdTime, int tier) {
        MachineDefinition def = DEFINITIONS.get(name);
        if (def == null) {
            throw new IllegalArgumentException("Unknown machine: " + name);
        }
        return def.createInstanceP(name, pos, item, state, baseProdTime, tier);
    }
       
    
    
    
    
}
