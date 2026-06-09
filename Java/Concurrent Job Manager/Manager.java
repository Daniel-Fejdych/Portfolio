

public interface Manager {
	//This interface MUST not be changed in anyway
	//Changing this interface will likely cause a compile failure when we try to compile your JobManager.java
	//and if so, will not be marked
	
	public void specifyJob(JobRequest job);
	public String serverLogin(String type, int ID); 	
}


