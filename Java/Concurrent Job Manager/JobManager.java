// v001 11/10/2024

	//	To implement the required concurrent functionality, your JobManager must use two Extrinsic Monitor classes:
	//			java.util.concurrent.locks.Condition;
	//			java.util.concurrent.locks.ReentrantLock;
	//	Note that you must not use the signalAll() method (as this creates inefficient polling activity).
	//
	//	No other thread-safe,  synchronised or scheduling classes or methods may be used. In particular:
	//	•	The keyword synchronized, and other classes from the package java.util.concurrent must be not be used. 
	//	•	Thread.Sleep() and any other methods that affect thread scheduling must not be used.
	//	•	“Busy waiting” techniques, such as spinlocks, must not be used. 
	//	Other non-thread-safe classes from SE17 may be used, e.g. LinkedLists, HashMaps and ArrayLists 
 	//	(these are unsynchronised and therefore not thread-safe).

    //See the Coursework spec for full list of constraints marking penalties

import java.util.ArrayList; //non sync Lists
import java.util.Map.Entry; //non sync Map
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class JobManager implements Manager {
	
	final public ReentrantLock lock = createReentrantLock();
	final public Condition busy = lock.newCondition(); //Is working on starting jobs.
	final public Condition waiting = lock.newCondition(); //server is waiting until it is released.
	
	//variable to keep track of if a server has successfully awakened due to the signal
	boolean hasAwoken = false;
	
	//variable to keep track of currently worked on job name
	String cJob = null;
	
	ArrayList<JobRequest> jobQueue = new ArrayList<JobRequest>();
	
	//stores the highest id server found
	public Server highest = null;
	
	// Will be used to store a mapping of Server IDs and ServerType
	// Using a Server object (That are not yet released)
	public ArrayList<Server> ServerList = new ArrayList<Server> ();
	
	@Override
	public void specifyJob(JobRequest job) {
		lockReentrantLock();
		// Add job to jobQueue
		jobQueue.add(job);
		// See if any job is completable
		JobRequest completableJob = AttemptJobCompletion();
		// If it is, complete it
		if (completableJob != null) {completeJob(completableJob);}
		unlockReentrantLock();
	}

	@Override
	public String serverLogin(String type, int ID) {
		String jobName;
		lockReentrantLock();
		// Add server to server list
		addServer(ID, type);
		// See if any job is completable
		JobRequest completableJob = AttemptJobCompletion();
		// If it is,
		if (completableJob != null) {
			// Check if this server is part of the request.
			if (completableJob.containsKey(type) && getHighestServer(type).id == ID) {//if current server is expected to work a job
				// Assume this server will fill that role
				completableJob.replace(type, completableJob.get(type) - 1);
				// Finally complete the job
				completeJob(completableJob);
				//  ...and return that job's name
				jobName = completableJob.jobName;
			}
			else {
				// Finally complete the job
				completeJob(completableJob);
				// ... and wait for a job to release it.
				await(ID, type); // Wait till it is needed, but make sure it has the highest id AND server type is correct
				jobName = cJob;
				// Inform job requester their request for this server has been completed
				hasAwoken = true;
			}
			
		}
		else {
			// If there is no completable job, then the server should just wait for a job to release it
			await(ID, type); // Wait till it is needed, but make sure it has the highest id AND server type is correct
			jobName = cJob;
			// Inform job requester their request for this server has been completed
			hasAwoken = true;
		}
		unlockReentrantLock();		
		return jobName;		
	}

	
	


	//==================================== PRIVATE METHODS & CLASSES  ===============================================
	
	// Your inner classes and private methods here
	
	// Method to check if any and which job request can be completed
	// Returns the first valid one as there should never be a situation that
	// two job request are valid simultaneously.
	
	public JobRequest AttemptJobCompletion() {
		if (cJob != null) {
			// Somebody is starting jobs, wait until they finish
			awaitBusy();
		}
		
		boolean passed = true;
		String type;
		int amount;
		// Loop through the jobQueue to find a valid job
		for (JobRequest jr : jobQueue) {
			passed = true;
			for (Entry<String, Integer> ta : jr.entrySet()) {
				type = ta.getKey();
				amount = ta.getValue();
				if (amount > GetActiveServerAmount(type)) {
					passed = false;
				}
			}
			if (passed) {
				// Found a valid job
				return jr;
			}
		}
		// Did not find a valid job
		return null;
	}
	

	
	public void completeJob(JobRequest job) {
				
		//job is being completed, remove from job queue.
		jobQueue.remove(job);
		
		//Brute - force approach
		cJob = job.jobName;
		
		for (Entry<String, Integer> ta : job.entrySet()) { // For each server type necessary,
			for (int i = 0; i < ta.getValue(); i++) {// loop for the number of servers needed.
				
				// Mark that the server has been used.
				removeServer(getHighestServer(ta.getKey()).id, ta.getKey());
				
				//release correct server threads using signal and Condition Reentrant locks
				hasAwoken = false;
				while(!hasAwoken) {
					waiting.signal(); 
					unlockReentrantLock();
					lockReentrantLock();
				}
			}
		}
		// Inform the rest it is done with its job
		cJob = null;
		busy.signal();
		
	}
	
	// Method to create the reentrant lock
	public ReentrantLock createReentrantLock() {
		ReentrantLock lock = new ReentrantLock();
		return lock;
	}
	
	// Method to lock the reentrant lock
	public void lockReentrantLock() {
		lock.lock();
	}
	
	// Method to unlock the reentrant lock
	public void unlockReentrantLock() {
		lock.unlock();
	}
	

	// Method to deal with adding items to the server list
	public void addServer(int id, String type) {
		ServerList.add(new Server(id, type));
	}
	
	// Method to deal with removing the first server from the server list of that id and type
	public void removeServer(int id, String type) {
		for (Server server : ServerList) {
			if (server.id == id && server.type.equals(type)){
				ServerList.remove(server);
				return;
			}
		}
		
	}
	
	// Method to return and set the highest variable to the highest id server of that type 
	public Server getHighestServer(String type) {
		Server chigh = null;
		for (Server server : ServerList) {
			if (server.type == type && (chigh == null || chigh.id < server.id)) {	
				chigh = server;
			}
			highest = chigh;
		}
		return highest;
	}	
	
	// Method to return the number of active servers of that type
	public int GetActiveServerAmount(String type) {
		int numServers = 0;
		for (Server server : ServerList) {
			if (server.type == type) {
				numServers += 1;
			}
		}
		return numServers;
	}
	
	// Method to await until a server of ID and type is required
	public void await(int ID, String type) {
		try {
			while(highest == null || ID != highest.id || !(highest.type.equals(type)) || hasAwoken == true) {
			waiting.await();
			}
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
	}
	
	// Method to await until thread or main's complete job is completed.
	public void awaitBusy() {
		try {
			busy.await();
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
	}
	
	// Custom class to store current servers while allowing duplicate servers.
	public class Server {
		public int id;
		public String type;
		public Server(int ServerID, String ServerType) {
			this.id = ServerID;
			this.type = ServerType;
		}
	}
}
