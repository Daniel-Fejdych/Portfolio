package ticTacToe;

import java.util.HashMap;
import java.util.List;
import java.util.Random;
import java.util.Map.Entry;

/**
 * A Q-Learning agent with a Q-Table, i.e. a table of Q-Values. This table is implemented in the {@link QTable} class.
 * 
 *  The methods to implement are: 
 * (1) {@link QLearningAgent#train}
 * (2) {@link QLearningAgent#extractPolicy}
 * 
 * Your agent acts in a {@link TTTEnvironment} which provides the method {@link TTTEnvironment#executeMove} which returns an {@link Outcome} object, in other words
 * an [s,a,r,s']: source state, action taken, reward received, and the target state after the opponent has played their move. You may want/need to edit
 * {@link TTTEnvironment} - but you probably won't need to. 
 * @author ae187
 */

public class QLearningAgent extends Agent {
	
	/**
	 * The learning rate, between 0 and 1.
	 */
	double alpha=0.1;
	
	/**
	 * The number of episodes to train for
	 */
	int numEpisodes=10000;
	
	/**
	 * The discount factor (gamma)
	 */
	double discount=0.9;
	
	
	/**
	 * The epsilon in the epsilon greedy policy used during training.
	 */
	double epsilon=0.1;
	
	/**
	 * This is the Q-Table. To get an value for an (s,a) pair, i.e. a (game, move) pair.
	 * 
	 */
	
	QTable qTable=new QTable();
	
	
	/**
	 * This is the Reinforcement Learning environment that this agent will interact with when it is training.
	 * By default, the opponent is the random agent which should make your q learning agent learn the same policy 
	 * as your value iteration and policy iteration agents.
	 */
	TTTEnvironment env=new TTTEnvironment();
	
	
	/**
	 * Construct a Q-Learning agent that learns from interactions with {@code opponent}.
	 * @param opponent the opponent agent that this Q-Learning agent will interact with to learn.
	 * @param learningRate This is the rate at which the agent learns. Alpha from your lectures.
	 * @param numEpisodes The number of episodes (games) to train for
	 */
	public QLearningAgent(Agent opponent, double learningRate, int numEpisodes, double discount)
	{
		env=new TTTEnvironment(opponent);
		this.alpha=learningRate;
		this.numEpisodes=numEpisodes;
		this.discount=discount;
		initQTable();
		train();
	}
	
	/**
	 * Initialises all valid q-values -- Q(g,m) -- to 0.
	 *  
	 */
	
	protected void initQTable()
	{
		List<Game> allGames=Game.generateAllValidGames('X');//all valid games where it is X's turn, or it's terminal.
		for(Game g: allGames)
		{
			List<Move> moves=g.getPossibleMoves();
			for(Move m: moves)
			{
				this.qTable.addQValue(g, m, 0.0);
				//System.out.println("initing q value. Game:"+g);
				//System.out.println("Move:"+m);
			}
			
		}
		
	}
	
	/**
	 * Uses default parameters for the opponent (a RandomAgent) and the learning rate (0.2). Use other constructor to set these manually.
	 */
	public QLearningAgent()
	{
		this(new RandomAgent(), 0.1, 100, 0.9);
		
	}
	
	
	/**
	 *  Implement this method. It should play {@code this.numEpisodes} episodes of Tic-Tac-Toe with the TTTEnvironment, updating q-values according 
	 *  to the Q-Learning algorithm as required. The agent should play according to an epsilon-greedy policy where with the probability {@code epsilon} the
	 *  agent explores, and with probability {@code 1-epsilon}, it exploits. 
	 *  
	 *  At the end of this method you should always call the {@code extractPolicy()} method to extract the policy from the learned q-values. This is currently
	 *  done for you on the last line of the method.
	 */
	
	public void train()
	{
		Random rn = new Random();
		//Works with enough episodes, 10 million in this case. 
		for(int i = 0; i < numEpisodes * 1000; i++) {
			while (!env.isTerminal()) {
				Game cGame = env.getCurrentGameState().clone();
				Move cMove = null;
				List <Move> pMoves = env.getPossibleMoves();
				//Makes the decision between explore and exploit using the epsilon-greedy policy
				if(rn.nextDouble() < epsilon) {
					//explore - pick a random action
					cMove = pMoves.get(rn.nextInt(pMoves.size()));
				}
				else {
					//exploit - pick current best action
					double bestQ = Double.NEGATIVE_INFINITY;
					for (Move pMove: pMoves) {
						double cQ = qTable.getQValue(cGame, pMove);
						if (bestQ < cQ) {
							bestQ = cQ;
							cMove = pMove;
						}
					}
				}

				//Does the move that was picked.
				Outcome o = null;
				try {
					o = env.executeMove(cMove);
					
				} catch (IllegalMoveException e) {
					//should never happen as only working moves get executed.
					e.printStackTrace();
				}
				
				Game nGame = env.getCurrentGameState();
				//Reward state for result by Updating its Q-value using the Q-learning rule
				//Uses the full Q-value reward calculation process.
				double oldQ = qTable.getQValue(cGame, cMove);
				
				//get the best Q-value possible in the new state
				nGame = env.getCurrentGameState();
				List <Move> newPMoves = env.getPossibleMoves();
				double newBestQ = Double.NEGATIVE_INFINITY;
				if (newPMoves.size() == 0) {
					newBestQ = 0;
					// state is unnecessary as some transition
					//to that state should already give a reward or punishment.
				}
				//The the best Q-value available for the new state.
				for (Move newPMove: newPMoves) {
					double cQ = qTable.getQValue(nGame, newPMove);
					if (newBestQ < cQ) {
						newBestQ = cQ;
					}
				}
				//Uses the Q-learning formula to adjust the qTable
				double sample = o.localReward + discount * newBestQ;
				qTable.addQValue(cGame, cMove, (1 - alpha) * oldQ + alpha * sample);
				
			
			}
			//resets the game to the initial state to allow for a new game to start.
			env.reset();
		}
		
		//--------------------------------------------------------
		//you shouldn't need to delete the following lines of code.
		this.policy=extractPolicy();
		if (this.policy==null)
		{
			System.out.println("Unimplemented methods! First implement the train() & extractPolicy methods");
			//System.exit(1);
		}
	}
	
	/** Implement this method. It should use the q-values in the {@code qTable} to extract a policy and return it.
	 *
	 * @return the policy currently inherent in the QTable
	 */
	public Policy extractPolicy()
	{
		//Extracts the policy from the Q-Table using expectiMax.
		HashMap<Game, Move> curPolicy = new HashMap<Game, Move>();
		for (Entry<Game, HashMap<Move, Double>> e: this.qTable.entrySet()) {
			Game cGame = e.getKey();
			//Stores best move and Q-value
			Move bestMove = null;
			double bestValue = Double.NEGATIVE_INFINITY;
			for (Entry<Move, Double> mv: e.getValue().entrySet()) {
				if (mv.getValue() > bestValue) { //If a better Q-value was found, save it.
					bestValue = mv.getValue();
					bestMove = mv.getKey();
				}
				
			}
			//Saves best move from state to the policy.
			curPolicy.put(cGame, bestMove);
		}
		//Returns the new policy.
		return new Policy(curPolicy);
		
	}
	
	public static void main(String a[]) throws IllegalMoveException
	{
		//Test method to play your agent against a human agent (yourself).
		QLearningAgent agent=new QLearningAgent();
		
		HumanAgent d=new HumanAgent();
		
		Game g=new Game(agent, d, d);
		g.playOut();
		
		
		

		
		
	}
	
	
	


	
}
