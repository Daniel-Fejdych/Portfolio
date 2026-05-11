package main;


import java.awt.Font;

import javax.swing.JTextField;

public class GameTextField extends JTextField{
	
	public GameTextField(String displayText, int initialFontSize, int columns){
		this.setText(displayText);//Sets text
		this.setHorizontalAlignment(JTextField.RIGHT);
		this.setFont(new Font("Serif", Font.PLAIN, initialFontSize));
		this.setOpaque(true);
	}
}
