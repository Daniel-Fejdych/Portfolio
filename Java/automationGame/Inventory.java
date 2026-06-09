package automationGame;

import java.util.ArrayList;
import java.util.List;

public class Inventory implements ItemHandler{
    private List<ItemStack> items;
    private int capacity;

    public Inventory(int capacity) {
        this.capacity = capacity;
        this.items = new ArrayList<>();
    }
    
    public List<ItemStack> getStacks() {
    	return items;
    }

    public boolean addItem(Item item, ItemState state, int amount) {
        // Try stacking first
        for (ItemStack stack : items) {
            if (stack.getItem().getId().equals(item.getId())
                && stack.getQuantity() < item.getMaxStackSize()
                && stack.getState().equals(state)) {

                stack.add(amount);
                return true;
            }
        }

        // Add new stack if space available
        if (items.size() < capacity) {
            items.add(new ItemStack(item, state, amount));
            return true;
        }

        return false; // Inventory full
    }
    

    public boolean removeItem(String itemId, int amount) {
        for (ItemStack stack : items) {
            if (stack.getItem().getId().equals(itemId)) {
                stack.remove(amount);

                if (stack.getQuantity() == 0) {
                    items.remove(stack);
                }
                return true;
            }
        }
        return false;
    }

    public void printInventory() {
        System.out.println("Inventory:");
        for (ItemStack stack : items) {
            System.out.println(
                stack.getItem().getName() + " x" + stack.getQuantity() + " of type " + stack.getState()
            );
        }
    }
    
    public boolean hasItem(String itemId, ItemState state, int amount) {
        int count = 0;
        for (ItemStack stack : items) {
            if (stack.getItem().getId().equals(itemId) && stack.getState().equals(state)) {
                count += stack.getQuantity();
            }
        }
        return count >= amount;
    }

    public void removeItemExact(String itemId, ItemState state, int amount) {
        for (int i = 0; i < items.size() && amount > 0; i++) {
            ItemStack stack = items.get(i);
            if (stack.getItem().getId().equals(itemId) && stack.getState().equals(state)) {
                int removed = Math.min(stack.getQuantity(), amount);
                stack.remove(removed);
                amount -= removed;

                if (stack.getQuantity() == 0) {
                    items.remove(i);
                    i--;
                }
            }
        }
    }
    
    public int countMatching(Ingredient ingredient) {
        int count = 0;
        for (ItemStack stack : items) {
            if (ingredient.matches(stack)) {
                count += stack.getQuantity();
            }
        }
        return count;
    }
    
    public void removeMatching(Ingredient ingredient) {
        int remaining = ingredient.getAmount();

        for (int i = 0; i < items.size() && remaining > 0; i++) {
            ItemStack stack = items.get(i);
            if (ingredient.matches(stack)) {
                int removed = Math.min(stack.getQuantity(), remaining);
                stack.remove(removed);
                remaining -= removed;

                if (stack.getQuantity() == 0) {
                    items.remove(i);
                    i--;
                }
            }
        }
    }
    public List<ItemStack> findMatching(Ingredient ingredient) {
        List<ItemStack> result = new ArrayList<>();
        for (ItemStack stack : items) {
            if (ingredient.matches(stack)) {
                result.add(stack);
            }
        }
        return result;
    }
    
    public void removeStack(ItemStack stack) {
        items.remove(stack);
    }
    
    public boolean canExtract() {
        return !items.isEmpty();
    }

    public ItemStack extractOne() {
        if (items.isEmpty()) return null;

        ItemStack stack = items.get(0);

        ItemStack extracted = new ItemStack(
                stack.getItem(),
                stack.getState(),
                1
        );

        stack.remove(1);
        if (stack.getQuantity() == 0) {
            items.remove(0);
        }

        return extracted;
    }

    public boolean canInsert(ItemStack stack) {
        return true; // later: filters, side rules, etc.
    }

    public void insertOne(ItemStack stack) {
        addItem(stack.getItem(), stack.getState(), 1);
    }
    
    public int getTotalItemCount() {
        return items.stream().mapToInt(ItemStack::getQuantity).sum();
    }
    public boolean exists(){
    	return capacity != 0;
    }
    public boolean isEmpty() {
    	return items.isEmpty();
    }
    
	public ItemStack peek() {
		return items.getFirst();
	}

}
