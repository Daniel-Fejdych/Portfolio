package automationGame;

import java.util.HashMap;
import java.util.Map;

public class ItemRegistry {
    private static final Map<String, Item> ITEMS = new HashMap<>();

    public static void register(Item item) {
        ITEMS.put(item.getId(), item);
    }

    public static Item get(String id) {
        return ITEMS.get(id);
    }

    public static boolean exists(String id) {
        return ITEMS.containsKey(id);
    }
}

