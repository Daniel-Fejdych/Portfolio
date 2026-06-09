// v001 11/10/2024

import java.util.HashMap;

public class JobRequest extends HashMap<String, Integer>{
	//The HashMap is used to store multiple Server type requirements for a job.
	//e.g. 
	//	JobRequest job01 = new JobRequest("job01");
	//	job01.put("ComputeServer", 2);
	//	job01.put("StorageServer", 1);	
	//
	// creates a JobRequest, named "job01", that requires two Compute Servers and one Storage Server.
	
	String jobName = "";	
	JobRequest(String job){
		super();
		this.jobName = job;
	}
    @Override
    public String toString() {
        return  "jobName=" + jobName + ", job=" + super.toString();
    }
    @Override
    public JobRequest clone() {
        JobRequest cloned = (JobRequest) super.clone();
        cloned.jobName = this.jobName;
        return cloned;
    }
}
