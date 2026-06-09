package automationGame;

import com.google.gson.*;
import java.io.FileReader;
import java.util.*;

public class ContentLoader {

    public static void loadAll(
            String itemsPath,
            String recipesPath,
            String machinesPath
    ) throws Exception {
        loadItems(itemsPath);
        loadRecipes(recipesPath);
        loadMachines(machinesPath);
    }

    // =========================================================
    // ITEMS
    // =========================================================
    private static void loadItems(String path) throws Exception {
        JsonObject root = JsonParser
                .parseReader(new FileReader(path))
                .getAsJsonObject();

        JsonArray items = root.getAsJsonArray("items");

        for (JsonElement e : items) {
            JsonObject obj = e.getAsJsonObject();

            String id = obj.get("id").getAsString();
            String name = obj.get("name").getAsString();
            int maxStack = obj.get("maxStack").getAsInt();

            Set<String> tags = new HashSet<>();
            for (JsonElement t : obj.getAsJsonArray("tags")) {
                tags.add(t.getAsString());
            }

            Set<ItemState> states = new HashSet<>();
            for (JsonElement s : obj.getAsJsonArray("states")) {
                states.add(ItemState.valueOf(s.getAsString()));
            }

            Item item = new Item(
                    id,
                    name,
                    maxStack,
                    tags,
                    states
            );

            ItemRegistry.register(item);
        }
    }

    // =========================================================
    // RECIPES
    // =========================================================
    private static void loadRecipes(String path) throws Exception {
        JsonObject root = JsonParser
                .parseReader(new FileReader(path))
                .getAsJsonObject();

        JsonArray recipes = root.getAsJsonArray("recipes");

        for (JsonElement e : recipes) {
            JsonObject obj = e.getAsJsonObject();
            String id = obj.get("id").getAsString();

            // ---------- Inputs ----------
            List<Ingredient> inputs = new ArrayList<>();
            for (JsonElement ing : obj.getAsJsonArray("inputs")) {
                JsonObject i = ing.getAsJsonObject();
                int amount = i.get("amount").getAsInt();

                if (i.has("item")) {
                    Item item = ItemRegistry.get(i.get("item").getAsString());
                    ItemState state = ItemState.valueOf(i.get("state").getAsString());
                    inputs.add(new ItemStateIngredient(item, state, amount));
                } else {
                    String tag = i.get("tag").getAsString();
                    ItemState state = ItemState.valueOf(i.get("state").getAsString());
                    inputs.add(new TagStateIngredient(tag, state, amount));
                }
            }

            // ---------- Outputs ----------
            Map<Item, Integer> outputs = new HashMap<>();
            if (obj.has("outputs")) {
                JsonObject outs = obj.getAsJsonObject("outputs");
                for (String key : outs.keySet()) {
                    outputs.put(
                            ItemRegistry.get(key),
                            outs.get(key).getAsInt()
                    );
                }
            }

            // ---------- State Transform ----------
            StateTransform transform = null;
            if (obj.has("stateTransform")) {
                JsonObject t = obj.getAsJsonObject("stateTransform");
                transform = new StateTransform(
                        ItemState.valueOf(t.get("from").getAsString()),
                        ItemState.valueOf(t.get("to").getAsString())
                );
            }

            int craftTime = obj.get("craftTime").getAsInt();

            Recipe recipe = new Recipe(
                    inputs,
                    outputs,
                    transform,
                    craftTime
            );

            RecipeRegistry.register(id, recipe);
        }
    }

    // =========================================================
    // MACHINES
    // =========================================================
    private static void loadMachines(String path) throws Exception {
        JsonObject root = JsonParser
                .parseReader(new FileReader(path))
                .getAsJsonObject();

        JsonArray machines = root.getAsJsonArray("machines");

        for (JsonElement e : machines) {
            JsonObject obj = e.getAsJsonObject();

            String id = obj.get("id").getAsString();
            int inputSize = obj.get("inputSize").getAsInt();
            int outputSize = obj.get("outputSize").getAsInt();

            List<Recipe> recipes = new ArrayList<>();
            for (JsonElement r : obj.getAsJsonArray("recipes")) {
                recipes.add(RecipeRegistry.get(r.getAsString()));
            }

            MachineDefinition def = new MachineDefinition(
                    id,
                    inputSize,
                    outputSize,
                    recipes
            );

            MachineRegistry.register(def);
        }
    }
}
