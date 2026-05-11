package gRpg;

import java.util.*;

public class Room{
	HashMap<String, Room> waysOut = new HashMap<String, Room>();
	Room() {
		waysOut.put("around", this);
	}
	Room(HashMap<String, Room> wOut) {
		waysOut = wOut;
	}
}
