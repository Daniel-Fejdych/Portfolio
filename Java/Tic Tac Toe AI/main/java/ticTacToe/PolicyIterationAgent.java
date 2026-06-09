package ticTacToe;


import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Random;
import java.util.Map.Entry;
/**
 * A policy iteration agent. You should implement the following methods:
 * (1) {@link PolicyIterationAgent#evaluatePolicy}: this is the policy evaluation step from your lectures
 * (2) {@link PolicyIterationAgent#improvePolicy}: this is the policy improvement step from your lectures
 * (3) {@link PolicyIterationAgent#train}: this is a method that should runs/alternate (1) and (2) until convergence. 
 * 
 * NOTE: there are two types of convergence involved in Policy Iteration: Convergence of the Values of the current policy, 
 * and Convergence of the current policy to the optimal policy.
 * The former happens when the values of the current policy no longer improve by much (i.e. the maximum improvement is less than 
 * some small delta). The latter happens when the policy improvement step no longer updates the policy, i.e. the current policy 
 * is already optimal. The algorithm should stop when this happens.
 * 
 * @author ae187
 *
 */
public class PolicyIterationAgent extends Agent {

	/**
	 * This map is used to store the values of states according to the current policy (policy evaluation). 
	 */
	HashMap<Game, Double> policyValues=new HashMap<Game, Double>();
	
	/**
	 * This stores the current policy as a map from {@link Game}s to {@link Move}. 
	 */
	HashMap<Game, Move> curPolicy=new HashMap<Game, Move>();
	
	double discount=0.9;
	
	/**
	 * The mdp model used, see {@link TTTMDP}
	 */
	TTTMDP mdp;
	
	/**
	 * loads the policy from file if one exists. Policies should be stored in .pol files directly under the project folder.
	 */
	public PolicyIterationAgent() {
		super();
		this.mdp=new TTTMDP();
		initValues();
		initRandomPolicy();
		train();
		
		
	}
	
	
	/**
	 * Use this constructor to initialise your agent with an existing policy
	 * @param p
	 */
	public PolicyIterationAgent(Policy p) {
		super(p);
		
	}

	/**
	 * Use this constructor to initialise a learning agent with default MDP paramters (rewards, transitions, etc) as specified in 
	 * {@link TTTMDP}
	 * @param discountFactor
	 */
	public PolicyIterationAgent(double discountFactor) {
		
		this.discount=discountFactor;
		this.mdp=new TTTMDP();
		initValues();
		initRandomPolicy();
		train();
	}
	/**
	 * Use this constructor to set the various parameters of the Tic-Tac-Toe MDP
	 * @param discountFactor
	 * @param winningReward
	 * @param losingReward
	 * @param livingReward
	 * @param drawReward
	 */
	public PolicyIterationAgent(double discountFactor, double winningReward, double losingReward, double livingReward, double drawReward)
	{
		this.discount=discountFactor;
		this.mdp=new TTTMDP(winningReward, losingReward, livingReward, drawReward);
		initValues();
		initRandomPolicy();
		train();
	}
	/**
	 * Initialises the {@link #policyValues} map, and sets the initial value of all states to 0 
	 * (V0 under some policy pi ({@link #curPolicy} from the lectures). Uses {@link Game#inverseHash} and {@link Game#generateAllValidGames(char)} to do this. 
	 * 
	 */
	public void initValues()
	{
		List<Game> allGames=Game.generateAllValidGames('X');//all valid games where it is X's turn, or it's terminal.
		for(Game g: allGames)
			this.policyValues.put(g, 0.0);
		
	}
	
	/**
	 *  You should implement this method to initially generate a random policy, i.e. fill the {@link #curPolicy} for every state. Take care that the moves you choose
	 *  for each state ARE VALID. You can use the {@link Game#getPossibleMoves()} method to get a list of valid moves and choose 
	 *  randomly between them. 
	 */
	public void initRandomPolicy()
	{
		//Fills the policy with random moves.
		Random rn = new Random();
		for (Entry<Game, Double> e: policyValues.entrySet()) {
			//picks a random move from the valid moves.
			Game cGame = e.getKey();
			List<Move> moves = cGame.getPossibleMoves();
			if (moves.size() != 0) { //if there are moves to do,
				curPolicy.put(cGame,moves.get(rn.nextInt(moves.size())));
			}
			else {
				curPolicy.put(cGame, null);//state that should not even be reached in any normal game.
			}
		}
		
		
	}
	
	
	/**
	 * Performs policy evaluation steps until the maximum change in values is less than {@code delta}, in other words
	 * until the values under the currrent policy converge. After running this method, 
	 * the {@link PolicyIterationAgent#policyValues} map should contain the values of each reachable state under the current policy. 
	 * You should use the {@link TTTMDP} {@link PolicyIterationAgent#mdp} provided to do this.
	 *
	 * @param delta
	 */
	protected void evaluatePolicy(double delta)
	{
		//Until the max change is below delta, keep applying the policy and wait for the values to converge.
		double maxChange = Double.POSITIVE_INFINITY;
		while (maxChange > delta){
			maxChange = 0; //stores the maximum absolute change observed.
			for (Entry<Game, Double> e: policyValues.entrySet()) {
				Game cGame = e.getKey();
				Double bestValue = Double.NEGATIVE_INFINITY;//!! origin 0 or Double.NEGATIVE_INFINITY
				//if terminal, set value to correct state.
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
				//else calculate it recursively
				double valOfState = 0;
				//Uses the same idea as the value iteration calculation.
				for(TransitionProb transition: mdp.generateTransitions(cGame, curPolicy.get(cGame))) {
					valOfState += transition.prob * (transition.outcome.localReward + discount * policyValues.get(transition.outcome.sPrime));
				}
				double v1 = valOfState;
				double v2 = policyValues.get(cGame);
				e.setValue(v1);
				//calculates the change using a math formula.
				double cChange = Math.abs((v1 - v2)/(v1 + v2));
				//keeps track of the highest change
				if (cChange > maxChange) {
					maxChange = cChange;
				}
			}
		}
		
		
	}
		
	
	
	/**This method should be run AFTER the {@link PolicyIterationAgent#evaluatePolicy} train method to improve the current policy according to 
	 * {@link PolicyIterationAgent#policyValues}. You will need to do a single step of expectimax from each game (state) key in {@link PolicyIterationAgent#curPolicy} 
	 * to look for a move/action that potentially improves the current policy. 
	 * 
	 * @return true if the policy improved. Returns false if there was no improvement, i.e. the policy already returned the optimal actions.
	 */
	protected boolean improvePolicy()
	{
		//copy the policy for comparison
		HashMap<Game, Move> oldPolicy = new HashMap<Game, Move>(curPolicy);
		//for each state, run expectiMax to get an improved move, if one exists.
		for (Entry<Game, Move> e: curPolicy.entrySet()) {
			Game cGame = e.getKey();
			//Store the best move and value
			Move bestMove = null;
			Double bestValue = Double.NEGATIVE_INFINITY;
			
			for(Move move: cGame.getPossibleMoves()) {
				double valOfState = 0;
				for(TransitionProb transition: mdp.generateTransitions(cGame, move)) {
					valOfState += transition.prob * policyValues.get(transition.outcome.sPrime);
				}
				if (valOfState > bestValue) {
					bestMove = move;
					bestValue = valOfState;
				}
			
			}
			//save the best moves to the policy.
			curPolicy.put(cGame, bestMove);
		}
		//the policy has not improved.
		if (oldPolicy.equals(curPolicy)) {
			return false;
		}
		//the policy has improved.
		return true;
	}
	
	/**
	 * The (convergence) delta
	 */
	double delta=0.1;
	
	/**
	 * This method should perform policy evaluation and policy improvement steps until convergence (i.e. until the policy
	 * no longer changes), and so uses your 
	 * {@link PolicyIterationAgent#evaluatePolicy} and {@link PolicyIterationAgent#improvePolicy} methods.
	 */
	public void train()
	{
		//Loop between evaluatePolicy and improvePolicy until
		//improvePolicy returns false (policy is optimal) and then save the policy.
		do {
			evaluatePolicy(delta);
		}
		while(improvePolicy());
		
		super.policy = new Policy(curPolicy);
		
		
	}
	
	public static void main(String[] args) throws IllegalMoveException
	{
		/**
		 * Test code to run the Policy Iteration Agent against a Human Agent.
		 */
		PolicyIterationAgent pi=new PolicyIterationAgent();
		
		HumanAgent h=new HumanAgent();
		
		Game g=new Game(pi, h, h);
		
		g.playOut();
		
		
	}
	

}
