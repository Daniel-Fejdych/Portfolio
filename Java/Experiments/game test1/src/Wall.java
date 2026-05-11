public class Wall 
{
	public int width = 10;
	private String color = "White";
	Wall()
	{
		//code
	}
	Wall(String colour)
	{
		color = colour;
	}
	public void getColor()
	{
		System.out.println(color);
	}
	public void setColor(String colour)
	{
		color = colour;
	}
	public void kickWall()
	{
		System.out.println("ouch");
	}
	public void lookAt()
	{
		System.out.println("Look's bad.");
	}
}//Abstraction is hiding how a method works, only what it does.