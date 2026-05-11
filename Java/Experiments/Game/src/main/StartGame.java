package main;

import javax.swing.JFrame;

public class StartGame {
	public static void main(String[] args) {
		GameProgram g = new GameProgram();
		g.setSize(400, 600);
		g.setTitle("Game Program");
		g.setVisible(true);
		g.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

}
}
