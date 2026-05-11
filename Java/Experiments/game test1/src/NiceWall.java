public class NiceWall extends Wall
{
	public int nice = 0;
	public int width = 3;
	NiceWall()
	{
		//code
	}
	NiceWall(int niceness)
	{
		nice = niceness;
	}
	public void lookAt()
	{
		System.out.println("look's nice");
	}
}