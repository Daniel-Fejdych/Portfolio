package automationGame;

import java.util.HashMap;
import java.util.Map;

public class RecipeRegistry {
    private static final Map<String, Recipe> RECIPES = new HashMap<>();

    public static void register(String id, Recipe recipe) {
        RECIPES.put(id, recipe);
    }

    public static Recipe get(String id) {
        return RECIPES.get(id);
    }
}