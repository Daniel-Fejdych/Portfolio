package oop_last;

public class StartProgram implements Pet{
	public static void main(String[] args){
		String[] arr = {"a","b","c"};
		for (int i = 0; i < arr.length; i++) {
			System.out.println(String.valueOf((char)(i)));
			System.out.println(arr[i]);
		}
	}

	@Override
	public void pet() {
		System.out.println("hello!");
		
	}
}
