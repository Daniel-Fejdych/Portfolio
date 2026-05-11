package main;

import java.awt.Dimension;
import java.awt.Font;

import javax.swing.JButton;

public class GameButton extends JButton {

	public GameButton(String displayText, int initialFontSize) {
		this.setText(displayText);// Sets text
		this.setHorizontalAlignment(JButton.CENTER);
		this.setFont(new Font("Serif", Font.PLAIN, initialFontSize));
		this.setOpaque(true);
		this.setPreferredSize(new Dimension(400, 100));
	}

	public GameButton(String displayText, int initialFontSize, int hSize, int vSize) {
		this.setText(displayText);// Sets text
		this.setHorizontalAlignment(JButton.CENTER);
		this.setFont(new Font("Serif", Font.PLAIN, initialFontSize));
		this.setOpaque(true);
		this.setPreferredSize(new Dimension(hSize, vSize));
	}
}
