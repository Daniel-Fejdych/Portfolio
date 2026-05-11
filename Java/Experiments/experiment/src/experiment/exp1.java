package experiment;

import java.util.Scanner;
import java.lang.Math;

public class exp1 {
	public static void main(String[] args) {
	    int num, sum = 0;
	    boolean test = false;
	    Scanner in = new Scanner(System.in);
	    num = in.nextInt();
	    
	    for(int a=0; a<=num; a++) {
		    for(int[] i = {0,0,0,0}; i[3]<=Math.sqrt(a);) {
		    	if ((a == Math.pow(i[0],2)+Math.pow(i[1],2)+Math.pow(i[2],2)+Math.pow(i[3],2)) && !test) {
						System.out.println(a + " = " + i);
						test = true;
						sum += 1;

				}
		    	else {
		    		i[3] += 1;
		    	}
		    	for(int n = 0; n < i.length - 1; n++)
		    	{
		    		if (i[n] >=Math.sqrt(a)){
		    			i[n] = 0;
		    			i[n] += 1;
		    			System.out.println();
		    		}
		    	}
		    }
		    test = false;
	    }
	    System.out.println("No of missing nums:" + (num - sum + 1));
	}
}