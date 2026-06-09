package automationGame;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Factory {

    // Sparse spatial index
    private final Map<Position, WorldEntity> entities = new HashMap<>();

    private final List<Machine> machines = new ArrayList<>();
    private final List<Belt> belts = new ArrayList<>();

    // -----------------------------
    // Placement / Removal
    // -----------------------------

    public void addEntity(WorldEntity entity) {
        entities.put(entity.getPosition(), entity);

        if (entity instanceof Machine m) machines.add(m);
        if (entity instanceof Belt b) belts.add(b);

        updateBeltsAround(entity.getPosition());
    }

    public void removeEntity(Position pos) {
        WorldEntity entity = entities.remove(pos);
        if (entity == null) return;

        if (entity instanceof Machine m) machines.remove(m);
        if (entity instanceof Belt b) belts.remove(b);

        updateBeltsAround(pos);
    }

    // -----------------------------
    // Connectivity
    // -----------------------------

    private void updateBeltsAround(Position pos) {
        for (Position adj : pos.adjacent()) {
            WorldEntity e = entities.get(adj);
            if (e instanceof Belt belt) {
                belt.recalculateConnections(this);
            }
        }
    }

    public InventoryAccess getInventoryAccessAt(Position pos) {
        WorldEntity e = entities.get(pos);
        if (e instanceof InventoryAccess ia) {
            return ia;
        }
        return null;
    }

    // -----------------------------
    // Ticking
    // -----------------------------

    public void tick() {
        machines.forEach(Machine::tick);
        belts.forEach(Belt::tick);
    }
    
    public void printSliceAtY(int y) {

        // -----------------------------
        // Collect slice entities
        // -----------------------------
        Map<Position, WorldEntity> slice = new HashMap<>();

        for (var entry : entities.entrySet()) {
            if (entry.getKey().y() == y) {
                slice.put(entry.getKey(), entry.getValue());
            }
        }

        if (slice.isEmpty()) {
            System.out.println("No entities at y = " + y);
            return;
        }

        // -----------------------------
        // Compute bounds
        // -----------------------------
        int minX = Integer.MAX_VALUE;
        int maxX = Integer.MIN_VALUE;
        int minZ = Integer.MAX_VALUE;
        int maxZ = Integer.MIN_VALUE;

        for (Position p : slice.keySet()) {
            minX = Math.min(minX, p.x());
            maxX = Math.max(maxX, p.x());
            minZ = Math.min(minZ, p.z());
            maxZ = Math.max(maxZ, p.z());
        }

        int width = maxX - minX + 1;
        int height = maxZ - minZ + 1;

        String[][] grid = new String[height][width];
        WorldEntity[][] entityGrid = new WorldEntity[height][width];
        int[] columnWidths = new int[width];

        // -----------------------------
        // First pass: build strings
        // -----------------------------


        for (int z = maxZ; z >= minZ; z--) {
            for (int x = minX; x <= maxX; x++) {

                int row = maxZ - z;
                int col = x - minX;

                Position pos = new Position(x, y, z);
                WorldEntity entity = slice.get(pos);

                String raw;
                if (entity == null) {
                    raw = ".";
                } else if (entity instanceof Machine m) {
                    raw = formatMachine(m);
                } else if (entity instanceof Belt b) {
                    raw = formatBelt(b);
                } else if (entity instanceof Chest c) {
                    raw = formatChest(c);
                } else {
                    raw = "?";
                }

                grid[row][col] = raw;
                entityGrid[row][col] = entity;

                columnWidths[col] = Math.max(columnWidths[col], raw.length());
            }
        }
        // -----------------------------
        // Second pass: print aligned
        // -----------------------------
        System.out.println("=== Factory slice at y = " + y + " ===");

        for (int row = 0; row < height; row++) {
            for (int col = 0; col < width; col++) {

                String raw = grid[row][col];
                WorldEntity entity = entityGrid[row][col];

                String colored = colorize(entity, raw);

                int pad = columnWidths[col] - raw.length();

                System.out.print(colored);
                System.out.print(" ".repeat(pad + 2));
            }
            System.out.println();
        }
    }
    
    private String formatMachine(Machine m) {
        return String.format(
            "M[%s t%d | I:%d O:%d | %.0f%%]",
            m.getName(),
            m.tier.getTier(),
            m.getInputInventory().getTotalItemCount(),
            m.getOutputInventory().getTotalItemCount(),
            m.getProgressPercent()
        );
    }
    private String formatBelt(Belt b) {
        return String.format(
            "B[I:%d | %.0f%%]",
            b.getOutputInventory().getTotalItemCount(),
            b.getProgressPercent()
        );
    }
    private String formatChest(Chest c) {
        return String.format(
            "C[%d]",
            c.getInputInventory().getTotalItemCount()
        );
    }
    
	public void connectMachinesWithBelts(Position from, Position to, int baseMoveTime, int tier) {

// Ensure both endpoints exist and are machines/chests
		InventoryAccess start = getInventoryAccessAt(from);
		InventoryAccess end = getInventoryAccessAt(to);

		if (start == null || end == null) {
			throw new IllegalArgumentException("Both endpoints must be machines or chests");
		}

		int y = from.y();
		if (to.y() != y) {
			throw new IllegalArgumentException("Both machines must be on the same Y level");
		}

		Position current = from;

		List<Position> path = new ArrayList<>();

// -----------------------------
// Build shortest Manhattan path
// -----------------------------
		int dx = Integer.compare(to.x(), from.x());
		int dz = Integer.compare(to.z(), from.z());

// Move in X
		while (current.x() != to.x()) {
			current = new Position(current.x() + dx, y, current.z());
			path.add(current);
		}

// Move in Z
		while (current.z() != to.z()) {
			current = new Position(current.x(), y, current.z() + dz);
			path.add(current);
		}

// -----------------------------
// Place belts along the path
// -----------------------------
		Position prev = from;

		for (int i = 0; i < path.size(); i++) {
			Position pos = path.get(i);

// Skip final tile (occupied by output machine)
			if (pos.equals(to))
				break;

// Overwrite anything in the way
			removeEntity(pos);

			Belt belt = new Belt(pos, baseMoveTime, tier);
			addEntity(belt);

// Determine directions
			Direction inputDir = directionFrom(pos, prev);

			Position next = (i + 1 < path.size()) ? path.get(i + 1) : to;
			Direction outputDir = directionFrom(pos, next);

// Set priorities
			belt.setPreferredInput(inputDir, this);
			belt.setPreferredOutput(outputDir, this);

			prev = pos;
		}
	}
	private Direction directionFrom(Position from, Position to) {
	    int dx = to.x() - from.x();
	    int dy = to.y() - from.y();
	    int dz = to.z() - from.z();

	    if (dx == 1) return Direction.POS_X;
	    if (dx == -1) return Direction.NEG_X;
	    if (dy == 1) return Direction.POS_Y;
	    if (dy == -1) return Direction.NEG_Y;
	    if (dz == 1) return Direction.POS_Z;
	    if (dz == -1) return Direction.NEG_Z;

	    throw new IllegalArgumentException("Positions are not adjacent");
	}
	
	private String colorize(WorldEntity entity, String raw) {

	    if (entity == null) {
	        return Ansi.GRAY + raw + Ansi.RESET;
	    }
	    
	    if (entity instanceof Machine m && (m.getProgressPercent() == 0)) {
	        return Ansi.RED + raw + Ansi.RESET;
	    } //Come Back !!!

	    if (entity instanceof ProducerMachine) {
	        return Ansi.GREEN + raw + Ansi.RESET;
	    }

	    if (entity instanceof CrafterMachine) {
	        return Ansi.CYAN + raw + Ansi.RESET;
	    }

	    if (entity instanceof Belt) {
	        return Ansi.YELLOW + raw + Ansi.RESET;
	    }

	    if (entity instanceof Chest) {
	        return Ansi.BLUE + raw + Ansi.RESET;
	    }

	    return Ansi.WHITE + raw + Ansi.RESET;
	}
}