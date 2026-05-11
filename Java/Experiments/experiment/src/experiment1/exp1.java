package experiment1;

import java.util.*;
import java.lang.Math;

public class exp1 {
	public static void main(String[] args) {
		ArrayList<String> list = new ArrayList<>();
		list.add("Sta");
		list.add("Start");
		list.set(0,list.get(1));
		//for(int i; i< 100;i++){
			//list.set(0, i+"");
		//}
		for(String s : list) {
			System.out.println(s);
		}
		HashMap<String, Integer> phoneBook = new HashMap<>();
		for(int i = 0; i< 100;i++){
		phoneBook.put("Human"+i, i*10203509);
		}
		for(String k : phoneBook.keySet()) {
			System.out.println(k+": " + phoneBook.get(k));
		}
	}
}