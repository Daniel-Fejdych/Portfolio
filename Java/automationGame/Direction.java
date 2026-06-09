package automationGame;

public enum Direction {
    POS_X(1, 0, 0),
    NEG_X(-1, 0, 0),
    POS_Y(0, 1, 0),
    NEG_Y(0, -1, 0),
    POS_Z(0, 0, 1),
    NEG_Z(0, 0, -1);

    public final int dx, dy, dz;

    Direction(int dx, int dy, int dz) {
        this.dx = dx;
        this.dy = dy;
        this.dz = dz;
    }

    public Position offset(Position p) {
        return new Position(p.x() + dx, p.y() + dy, p.z() + dz);
    }
}
