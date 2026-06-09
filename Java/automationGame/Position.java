package automationGame;

import java.util.List;

public record Position(int x, int y, int z) {

    public List<Position> adjacent() {
        return List.of(
            new Position(x + 1, y, z),
            new Position(x - 1, y, z),
            new Position(x, y + 1, z),
            new Position(x, y - 1, z),
            new Position(x, y, z + 1),
            new Position(x, y, z - 1)
        );
    }
}
