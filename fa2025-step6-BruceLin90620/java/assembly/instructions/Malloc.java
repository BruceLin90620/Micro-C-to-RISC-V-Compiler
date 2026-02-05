package assembly.instructions;

public class Malloc extends Instruction {

    String src;
    String dest;

    /**
     * Models the magic instruction MALLOC
     */
    public Malloc(String src, String dest) {
        super();
        this.src = src;
        this.dest = dest;
        this.oc = OpCode.MALLOC;
    }

    /**
     * @return "HALT"
     */
    public String toString() {
        return String.valueOf(this.oc) + " " + dest + ", " + src;
    }
}
