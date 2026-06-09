package automationGame;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class InputForm extends JFrame {

    /**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private JComboBox<String> dropdown;
    private JTextField[] textFields = new JTextField[9];
    private JLabel[] inputLabels = new JLabel[9];
    private static Factory factory;

    public InputForm() {
        setTitle("Auto GUI Interface");
        setSize(400, 750);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Main panel
        JPanel panel = new JPanel();
        panel.setLayout(new GridLayout(11, 2, 10, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));

        // Dropdown menu (9 options)
        String[] options = {
                "craft", "prod", "chest", "belt",
                "delete", "wait", "print",
                "connect", "exit"
        };
        dropdown = new JComboBox<>(options);

        panel.add(new JLabel("Select an option:"));
        panel.add(dropdown);

        // Create labels and text fields
        for (int i = 0; i < 9; i++) {
            inputLabels[i] = new JLabel("Input " + (i + 1) + ":");
            textFields[i] = new JTextField();

            panel.add(inputLabels[i]);
            panel.add(textFields[i]);
        }

        // Submit button
        JButton submitButton = new JButton("Submit");


        submitButton.addActionListener(e -> handleSubmit());

        panel.add(new JLabel()); // empty cell
        panel.add(submitButton);

        // Listen for dropdown changes
        dropdown.addActionListener(e -> updateLabels());
        
        add(panel);
    }

    // Change labels based on dropdown selection
    private void updateLabels() {
        String selected = (String) dropdown.getSelectedItem();

        switch (selected) {
            case "craft":
            	setLabels("Name of Machine", " tier", "-", "x", "y", "z", "-", "-", "-");
                break;

            case "prod":
            	setLabels("Name of Item Produced", "Base Production Time", "tier", "x", "y", "z", "-", "-", "-");
                break;

            case "chest":
            	setLabels("Inventory Size", "-", "-", "x", "y", "z", "-", "-", "-");
                break;
                
            case "belt":
            	setLabels("Base Speed", "Tier", "-", "x", "y", "z", "-", "-", "-");
                break;
                
            case "delete":
            	setLabels("-", "-", "-", "x", "y", "z", "-", "-", "-");
                break;
                
            case "wait":
                setLabels("Number of ticks", "-", "-", "-", "-", "-", "-", "-", "-");
                break;
            
            case "print":
                setLabels("Y level", "-", "-", "-", "-", "-", "-", "-", "-");
                break;
                
            case "connect":
                setLabels("Base Speed", "Tier", "-", "x1", "y1", "z1", "x2", "y2", "z2");
                break;

            default:
                setLabels("-", "-", "-", "-", "-", "-", "-", "-", "-");
        }
    }

    private void setLabels(String l1, String l2, String l3,
                           String l4, String l5, String l6,
                           String l7, String l8, String l9) {
        inputLabels[0].setText(l1 + ":");
        inputLabels[1].setText(l2 + ":");
        inputLabels[2].setText(l3 + ":");
        inputLabels[3].setText(l4 + ":");
        inputLabels[4].setText(l5 + ":");
        inputLabels[5].setText(l6 + ":");
        inputLabels[6].setText(l7 + ":");
        inputLabels[7].setText(l8 + ":");
        inputLabels[8].setText(l9 + ":");
    }
    
    
    
    // Method called when button is pressed
    private void handleSubmit() {
        String selectedOption = (String) dropdown.getSelectedItem();

        String[] inputs = new String[10];
        inputs[0] = selectedOption;
        for (int i = 1; i < 10; i++) {
            inputs[i] = textFields[i-1].getText();
        }
        System.out.println("Selected option: " + String.join(" ", inputs));
        CommandProcessor.processUserInput(factory, String.join(" ", inputs));

        // You can now pass these values to any other method or logic
        processData(selectedOption, inputs);
    }

    // Example processing method
    private void processData(String option, String[] inputs) {
        JOptionPane.showMessageDialog(
                this,
                "Option: " + option + "\nFirst input: " + inputs[0],
                "Data Received",
                JOptionPane.INFORMATION_MESSAGE
        );
    }

    public static String main(Factory f) {
    	factory = f;
        SwingUtilities.invokeLater(() -> {
            new InputForm().setVisible(true);
        });
		return null;
    }
}
