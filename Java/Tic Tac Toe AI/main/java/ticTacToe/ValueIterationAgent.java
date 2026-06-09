package ticTacToe;


import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

/**
 * A Value Iteration Agent, only very partially implemented. The methods to implement are: 
 * (1) {@link ValueIterationAgent#iterate}
 * (2) {@link ValueIterationAgent#extractPolicy}
 * 
 * You may also want/need to edit {@link ValueIterationAgent#train} - feel free to do this, but you probably won't need to.
 * @author ae187
 *
 */
public class ValueIterationAgent extends Agent {

	/**
	 * This map is used to store the values of states
	 */
	Map<Game, Double> valueFunction=new HashMap<Game, Double>();
	
	/**
	 * the discount factor
	 */
	double discount=0.9;
	
	/**
	 * the MDP model
	 */
	TTTMDP mdp=new TTTMDP();
	
	/**
	 * the number of iterations to perform - feel free to change this/try out different numbers of iterations
	 */
	int k=10;
	
	
	/**
	 * This constructor trains the agent offline first and sets its policy
	 */
	public ValueIterationAgent()
	{
		super();
		mdp=new TTTMDP();
		this.discount=0.9;
		initValues();
		train();
	}
	
	
	/**
	 * Use this constructor to initialise your agent with an existing policy
	 * @param p
	 */
	public ValueIterationAgent(Policy p) {
		super(p);
		
	}

	public ValueIterationAgent(double discountFactor) {
		
		this.discount=discountFactor;
		mdp=new TTTMDP();
		initValues();
		train();
	}
	
	/**
	 * Initialises the {@link ValueIterationAgent#valueFunction} map, and sets the initial value of all states to 0 
	 * (V0 from the lectures). Uses {@link Game#inverseHash} and {@link Game#generateAllValidGames(char)} to do this. 
	 * 
	 */
	public void initValues()
	{
		
		List<Game> allGames=Game.generateAllValidGames('X');//all valid games where it is X's turn, or it's terminal.
		for(Game g: allGames)
			this.valueFunction.put(g, 0.0);//!!!originally 0.0
		
		
		
	}
	
	
	
	public ValueIterationAgent(double discountFactor, double winReward, double loseReward, double livingReward, double drawReward)
	{
		this.discount=discountFactor;
		mdp=new TTTMDP(winReward, loseReward, livingReward, drawReward);
	}
	
	/**
	 
	
	/*
	 * Performs {@link #k} value iteration steps. After running this method, the {@link ValueIterationAgent#valueFunction} map should contain
	 * the (current) values of each reachable state. You should use the {@link TTTMDP} provided to do this.
	 * 
	 *
	 */
	public void iterate()
	{
		//Iterates k times for correct depth.
		for (int i = 0; i < k; i++) {
			//Iterates for every entry in the valueFunction to check all states.
			for (Entry<Game, Double> e: valueFunction.entrySet()) {

				Game cGame = e.getKey();
				//Uses bestValue to keep track of the best value found.
				Double bestValue = Double.NEGATIVE_INFINITY;
				
				//if the game is terminal, set value to correct state.
				if (cGame.isTerminal()) {
					switch (cGame.state) {
						case Game.X_WON: e.setValue(mdp.winReward);
						continue;
						case Game.O_WON: e.setValue(mdp.loseReward);
						continue;
						default: e.setValue(mdp.livingReward);
						continue;
					}
				}

				for(Move move: cGame.getPossibleMoves()) {
					//Uses valOfState to calculate addition of potential transitions.
					double valOfState = 0;
					
					for(TransitionProb transition: mdp.generateTransitions(cGame, move)) {
						//for each possible transition,
						valOfState += transition.prob * (transition.outcome.localReward + discount * valueFunction.get(transition.outcome.sPrime));
						//Calculate the value of all possible transitions for an action.
						//Also, sum the values of all possible transitions for each move.
						//valOfState will sum to Q(s, a) as
						//Q(s, a) = sum (T(s, a, s`)[R(s, a, s`) + discount*V(s`)])

					}
					if (valOfState > bestValue) {
						bestValue = valOfState; //A better value has been found.

					}

				}
				//save the current game states value using the best move.
				e.setValue(bestValue);
			}
		}
	}

	/**This method should be run AFTER the train method to extract a policy according to {@link ValueIterationAgent#valueFunction}
	 * You will need to do a single step of expectimax from each game (state) key in {@link ValueIterationAgent#valueFunction} 
	 * to extract a policy.
	 * 
	 * @return the policy according to {@link ValueIterationAgent#valueFunction}
	 */
	public Policy extractPolicy()
	{
		//Uses expectiMax to get the best policy.
		HashMap<Game, Move> moveFunction = new HashMap<Game, Move>();
		for (Entry<Game, Double> e: valueFunction.entrySet()) {

			Game cGame = e.getKey();
			//Stores the best value and move
			Move bestMove = null;
			Double bestValue = Double.NEGATIVE_INFINITY;

			for(Move move: cGame.getPossibleMoves()) {
				double valOfState = 0;
				for(TransitionProb transition: mdp.generateTransitions(cGame, move)) {
					
					//for each possible transition
					valOfState += transition.prob * valueFunction.get(transition.outcome.sPrime);
					
					//Calculate the value of all possible transitions for an action.

				}
				if (valOfState > bestValue) {
					bestMove = move;
					bestValue = valOfState; //This time store the best move and the best value.
				}
				
			}
			//saves the best move for this game state to the moveFuction
			moveFunction.put(cGame, bestMove);
		}
		Policy p = new Policy(moveFunction);
		
		return p;
	}
	
	/**
	 * This method solves the mdp using your implementation of {@link ValueIterationAgent#extractPolicy} and
	 * {@link ValueIterationAgent#iterate}. 
	 */
	public void train()
	{
		/**
		 * First run value iteration
		 */
		this.iterate();
		/**
		 * now extract policy from the values in {@link ValueIterationAgent#valueFunction} and set the agent's policy 
		 *  
		 */
		
		super.policy=extractPolicy();
		
		if (this.policy==null)
		{
			System.out.println("Unimplemented methods! First implement the iterate() & extractPolicy() methods");
			//System.exit(1);
		}
		
		
		
	}

	public static void main(String a[]) throws IllegalMoveException
	{
		//Test method to play the agent against a human agent.
		ValueIterationAgent agent=new ValueIterationAgent();
		HumanAgent d=new HumanAgent();
		
		Game g=new Game(agent, d, d);
		g.playOut();
		
		
		

		
		
	}
}
