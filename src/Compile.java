import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;

class Compile {
    public static void main(String[] args) {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new IllegalStateException("Compiler module absent");
        int status = compiler.run(null, null, null, "Hello.java");
        if (status != 0) throw new IllegalStateException("Compiler failed: " + status);
    }
}
