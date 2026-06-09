package automationGame;

public interface ItemHandler {
    boolean canExtract();
    ItemStack extractOne();
    boolean canInsert(ItemStack stack);
    void insertOne(ItemStack stack);
}