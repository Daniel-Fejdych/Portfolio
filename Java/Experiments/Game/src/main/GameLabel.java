package main;


import java.awt.Font;

import javax.swing.JLabel;

public class GameLabel extends JLabel{
	
	public GameLabel(String displayText, int initialFontSize) {
		this.setText(displayText);//Sets text
		this.setHorizontalAlignment(JLabel.RIGHT);
		this.setFont(new Font("Serif", Font.PLAIN, initialFontSize));
		this.setOpaque(true);
	}
}
