import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

class calculatorTestTest {

	@BeforeAll
	static void setUp() {
		calculatorTest c = new calculatorTest();
	}
	@Test
	void test() {
	}
	@Test
	void testAbs() {
		calculatorTest c = new calculatorTest();
		assertSame(1,c.abs(1));
		assertSame(-1,c.abs(1));
		assertSame(0,c.abs(0));
	}

}
