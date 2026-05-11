/**
 * 
 * Software Development 1, Coursework 1.
 * 
 * Make sure you read the specification document on
 * Canvas in full before starting this assessment.
 * 
 */
import java.util.Scanner;//Necessary to use Scanners
public class start {

	public static void main(String[] args) {
		String wall = "hello";
		String Out = helloWorld(wall);
		System.out.println(Out);
		Wall wall0;//This is not created, it = null
		wall0 = null;
		if(wall0 == null)
		{
			System.out.println("Error");
		}
		wall0 = new Wall();
		if(wall0 == null)
		{
			System.out.println("Error1");
		}
		Wall wall1 = new Wall();//
		//This is a reference variable
		//References the wall1 object, does not store it
		System.out.println(wall1.width);
		wall1 = wall0;//This is bad as now both wall1 and wall0 point to wall0, wall0 will be
		//cleaned 
	}
	public static String helloWorld(String In)
	{
		System.out.println(In);
		Wall wallO0 = new Wall(In);
		return In;
	}
	//Object Orientated Programming (OOP)
	//Object is a representation of an Entity
	//Objects can have an ID
	//Class is a blueprint for an Object

}