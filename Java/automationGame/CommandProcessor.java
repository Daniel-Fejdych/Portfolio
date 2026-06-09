package automationGame;

import java.util.Scanner;

public class CommandProcessor {
	private static int i(String in) {
		return Integer. parseInt(in);
	}
    public static boolean processUserInput(Factory factory, Scanner scanner) {
    	
			System.out.print("Enter command: ");
			String input = scanner.nextLine().trim();

			if (input.isEmpty()) {
			    System.out.println("No input provided.");
			    return true;
			}
			return processUserInput(factory, input);
			
    }			
    public static boolean processUserInput(Factory factory, String input) {
			// Split only on the first space
			String[] parts = input.split("\\s+", 2);
			String command = parts[0];
			String[] args = (parts.length > 1 ? parts[1] : "").split(" ");
			Machine m;
			
			//
			switch (command.toLowerCase()) {
			    case "craft":
			    	if(args.length < 5) {
			    		System.out.println("craft mName tier - x y z");
			    		break;
			    	}
			        System.out.println("ADD Crafter command received");	        
					m = MachineRegistry.create(args[0],
							new Position(i(args[3]), i(args[4]), i(args[5])),
							i(args[1]));
			    	factory.addEntity(m);
			        
			        break;
			    case "prod":
			    	if(args.length < 6) {
			    		System.out.println("prod iName bpTime tier x y z");
			    		break;
			    	}
			        System.out.println("ADD Producer command received");

			        m = MachineRegistry.createP("miner",
			        		new Position(i(args[3]), i(args[4]), i(args[5])),
			        		ItemRegistry.get(args[0]), ItemState.ORE, i(args[1]), i(args[2]));
			        

			        factory.addEntity(m);
			        break;
			       
				case "chest":
					
			    	if(args.length < 4) {
			    		System.out.println("chest iSize - - x y z");
			    		break;
			    	}
					
					System.out.println("ADD Chest command received");
					
					m = new Chest(new Position(i(args[3]), i(args[4]), i(args[5])), i(args[0]));

					factory.addEntity(m);
					break;
				case "belt":
					
			    	if(args.length < 5) {
			    		System.out.println("belt bSpeed tier - x y z");
			    		break;
			    	}
					
					System.out.println("ADD Belt command received");
					Belt belt = new Belt(new Position(i(args[3]), i(args[4]), i(args[5])),
							i(args[0]), i(args[1]));

					factory.addEntity(belt);
					break;
					
				case "connect":
					System.out.println("CONNECT Belts command received");
					factory.connectMachinesWithBelts(
						    new Position(i(args[3]), i(args[4]), i(args[5])),   // input machine
						    new Position(i(args[6]), i(args[7]), i(args[8])),  // output machine
						    i(args[0]),                      // baseMoveTime
						    i(args[1])                        // belt tier
						);
			    case "delete":
			        System.out.println("DELETE command received");
			        
			        break;

			    case "wait":
			        for(int i = 0; i< i(args[0]); i++) {
				        factory.tick();
			        }
			        factory.printSliceAtY(0);
			        break;
			    case "print":
				    factory.printSliceAtY(i(args[0]));

			        break;

			    case "exit":
			        System.out.println("Exiting program...");
			        return false;

			    default:
			        System.out.println("Unknown command: " + command);
			}
        return true;
    }
}
