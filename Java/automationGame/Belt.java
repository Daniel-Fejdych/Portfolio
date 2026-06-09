package automationGame;

import java.util.ArrayList;
import java.util.List;

public class Belt implements WorldEntity, InventoryAccess {
    private final Position position;
    
    private InventoryAccess input;
    private InventoryAccess output;
    
    private final MachineInventory buffer = new MachineInventory(1);
    
    private Direction preferredInputDir = null;
    private Direction preferredOutputDir = null;
    
    

    private final int baseMoveTime;
    private final double speedMultiplier;

    private double progress = 0;

    public Belt(Position position, int baseMoveTime, int tier) {
    	this.position = position;
        this.baseMoveTime = baseMoveTime;
        this.speedMultiplier = Math.pow(2, tier - 1);
    }

    // -----------------------------
    // Dynamic endpoint management
    // -----------------------------

    public void setInput(InventoryAccess input) {
        this.input = input;
        resetProgress();
    }

    public void setOutput(InventoryAccess output) {
        this.output = output;
        resetProgress();
    }

    public void clearInput() {
        this.input = null;
        resetProgress();
    }

    public void clearOutput() {
        this.output = null;
        resetProgress();
    }

    private void resetProgress() {
        this.progress = 0;
    }

    // -----------------------------
    // Tick logic
    // -----------------------------

    public void tick() {

        if (input == null || output == null) {
            progress = 0;
            return;
        }

        progress += speedMultiplier;
        if (progress < baseMoveTime) return;

        // -----------------------------
        // Phase 1: Pull into buffer
        // -----------------------------
        if (buffer.isEmpty()) {

            MachineInventory source = input.getOutputInventory();
            if (!source.canExtract()) {
                progress = 0;
                return;
            }

            ItemStack stack = source.extractOne();
            if (stack == null) {
                progress = 0;
                return;
            }

            buffer.insertOne(stack);
            progress -= baseMoveTime;
            return;
        }

        // -----------------------------
        // Phase 2: Push from buffer
        // -----------------------------
        MachineInventory target = output.getInputInventory();
        if (!target.canInsert(buffer.peek())) {
            progress = 0;
            return;
        }

        ItemStack stack = buffer.extractOne();
        target.insertOne(stack);

        progress -= baseMoveTime;
    }

    
    public void recalculateConnections(Factory world) {

        InventoryAccess newInput = null;
        InventoryAccess newOutput = null;

        boolean usedPreferred = false;

        // -----------------------------
        // Preferred input
        // -----------------------------
        if (preferredInputDir != null) {
            Position p = preferredInputDir.offset(position);
            InventoryAccess ia = world.getInventoryAccessAt(p);
            if (ia != null) {
                newInput = ia;
                usedPreferred = true;
            }
        }

        // -----------------------------
        // Preferred output
        // -----------------------------
        if (preferredOutputDir != null) {
            Position p = preferredOutputDir.offset(position);
            InventoryAccess ia = world.getInventoryAccessAt(p);
            if (ia != null) {
                newOutput = ia;
                usedPreferred = true;
            }
        }

        // -----------------------------
        // Fallback to automatic
        // -----------------------------
        if (!usedPreferred || newInput == null || newOutput == null) {
            autoRecalculate(world);
            return;
        }

        setInput(newInput);
        setOutput(newOutput);
    }
    
    private void autoRecalculate(Factory world) {

        List<InventoryAccess> candidates = new ArrayList<>();

        for (Position adj : position.adjacent()) {
            InventoryAccess ia = world.getInventoryAccessAt(adj);
            if (ia != null) {
                candidates.add(ia);
            }
        }

        InventoryAccess bestInput = null;
        int bestInputScore = Integer.MIN_VALUE;

        for (InventoryAccess ia : candidates) {
            int score = ia.getInputPriority();
            if (score > bestInputScore) {
                bestInputScore = score;
                bestInput = ia;
            }
        }

        InventoryAccess bestOutput = null;
        int bestOutputScore = Integer.MIN_VALUE;

        for (InventoryAccess ia : candidates) {
            if (ia == bestInput) continue; // 👈 key line

            int score = ia.getOutputPriority();
            if (score > bestOutputScore) {
                bestOutputScore = score;
                bestOutput = ia;
            }
        }

        // Fallback: only one neighbor exists
        if (bestOutput == null && bestInput != null && candidates.size() == 1) {
            bestOutput = bestInput;
        }

        setInput(bestInput);
        setOutput(bestOutput);
    }

    @Override
    public Position getPosition() {
        return position;
    }
    
    public double getProgressPercent() {
        if (input == null || output == null) return 0;
        return Math.min(100.0, (progress / baseMoveTime) * 100.0);
    }
    
    
    public void setPreferredInput(Direction dir, Factory world) {
        this.preferredInputDir = dir;
        recalculateConnections(world);
    }

    public void setPreferredOutput(Direction dir, Factory world) {
        this.preferredOutputDir = dir;
        recalculateConnections(world);
    }

    public void clearPreferredInput(Factory world) {
        this.preferredInputDir = null;
        recalculateConnections(world);
    }

    public void clearPreferredOutput(Factory world) {
        this.preferredOutputDir = null;
        recalculateConnections(world);
    }
    
    @Override
    public MachineInventory getInputInventory() {
        return buffer;
    }

    @Override
    public MachineInventory getOutputInventory() {
        return buffer;
    }

}