package main;
import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.GridLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JPanel;

public class GameProgram extends JFrame implements ActionListener {
	private JMenuBar menuBar;//all variable are private.
	private JMenu loadMenu;
	private JMenuItem openItem, exitItem;
	private GameLabel questionLabel, scoreLabel;
	private JPanel questionPanel, answerPanel, quizActionPanel;
	private GameButton nextButton;
	private GameButton[] answerButtonArray = new GameButton[4];
	private int currentQuestion = 0, correctQuestions = 0;
	final private int initialFontSize = 16;

	GameProgram() {

		setLayout(new FlowLayout());// Main section

		menuBar = new JMenuBar();
		loadMenu = new JMenu("File");
		openItem = new JMenuItem("Open");
		exitItem = new JMenuItem("Exit");

		openItem.addActionListener(this);
		exitItem.addActionListener(this);

		loadMenu.add(openItem);
		loadMenu.add(exitItem);

		menuBar.add(loadMenu);
		setJMenuBar(menuBar);


		questionPanel = new JPanel();
		questionPanel.setLayout(new FlowLayout());
		add(questionPanel);

		questionLabel = new GameLabel("No Quiz Loaded!", initialFontSize);
		scoreLabel = new GameLabel(correctQuestions + "/" + currentQuestion, initialFontSize);
		questionPanel.add(questionLabel);
		questionPanel.add(scoreLabel);

		answerPanel = new JPanel();
		answerPanel.setLayout(new GridLayout(4, 1));
		add(answerPanel);

		for (int i = 0; i < 4; i++) {
			answerButtonArray[i] = new GameButton("", initialFontSize);
			answerButtonArray[i].setEnabled(false);
			answerPanel.add(answerButtonArray[i]);
			answerButtonArray[i].addActionListener(this);

		}

		quizActionPanel = new JPanel();
		quizActionPanel.setLayout(new FlowLayout());
		nextButton = new GameButton("Next", initialFontSize);
		nextButton.addActionListener(this);
		quizActionPanel.add(nextButton);
		add(quizActionPanel);
	}


	@Override
	public void actionPerformed(ActionEvent event) {

	}
}
