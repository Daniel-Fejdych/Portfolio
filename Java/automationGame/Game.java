package automationGame;

import java.util.Scanner;

public class Game {
	
	
	
	
	

	
    public static void main(String[] args) {
    	
    	try {
			ContentLoader.loadAll("src\\automationGame\\items.json", "src\\automationGame\\recipes.json", "src\\automationGame\\machines.json");
		} catch (Exception e) {
			// Problem with files
			e.printStackTrace();
		}
    	
    	

    	Factory factory = new Factory();
//    	String machine = "press";
//    	int tier = 2;
//    	int x = 0;
//    	int y = 0;
//    	int z = 0;
//    	Machine m = MachineRegistry.create(
//    	        machine,
//    	        new Position(x, y, z),
//    	        tier
//    	);
//    	factory.addEntity(m);

    	
    	//press.inputInventory.addItem(ItemRegistry.get("iron"), ItemState.INGOT, 3);

    	InputForm.main(factory);
    	
    	

        Boolean ongoing = true;
        try (Scanner scanner = new Scanner(System.in)) {
        while (ongoing) {
        	//f.tick();
        	ongoing = CommandProcessor.processUserInput(factory, scanner);
            //ItemTransfer.move(ItemRegistry.get("iron"), ItemState.INGOT, 1, furnace.outputInventory, press.inputInventory);
        }
        }

    }
}
