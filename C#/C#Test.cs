using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;

namespace MathFunctionAnalyzer
{
    /// <summary>
    /// Analyzes a mathematical function of one variable (x) given as a string.
    /// Provides properties: derivative, domain, range, zeros, critical points, inflection points.
    /// </summary>
    public class FunctionAnalyzer
    {
        private readonly Func<double, double> _func;
        private readonly Func<double, double> _derivativeFunc;
        private readonly Func<double, double> _secondDerivativeFunc;
        private readonly string _originalExpression;
        private readonly string _derivativeExpression;
        private readonly string _secondDerivativeExpression;

        // Numerical method parameters
        private const double Epsilon = 1e-7;
        private const double DefaultRangeStart = -10.0;
        private const double DefaultRangeEnd = 10.0;
        private const int DefaultNumPoints = 1000;

        /// <summary>
        /// Initializes a new instance of the <see cref="FunctionAnalyzer"/> class.
        /// </summary>
        /// <param name="expression">Function expression in terms of 'x' (e.g., "x^2 + sin(x)").</param>
        /// <exception cref="ArgumentException">Thrown when expression is invalid.</exception>
        public FunctionAnalyzer(string expression)
        {
            _originalExpression = expression;
            var ast = Parser.Parse(expression);
            _func = ast.Compile();

            var derivativeAst = Differentiator.Differentiate(ast);
            _derivativeExpression = derivativeAst.ToString();
            _derivativeFunc = derivativeAst.Compile();

            var secondDerivativeAst = Differentiator.Differentiate(derivativeAst);
            _secondDerivativeExpression = secondDerivativeAst.ToString();
            _secondDerivativeFunc = secondDerivativeAst.Compile();
        }

        /// <summary>
        /// Evaluates the function at a given x.
        /// </summary>
        public double Evaluate(double x) => _func(x);

        /// <summary>
        /// Evaluates the first derivative at a given x.
        /// </summary>
        public double EvaluateDerivative(double x) => _derivativeFunc(x);

        /// <summary>
        /// Evaluates the second derivative at a given x.
        /// </summary>
        public double EvaluateSecondDerivative(double x) => _secondDerivativeFunc(x);

        /// <summary>
        /// Returns the symbolic derivative as a string.
        /// </summary>
        public string Derivative => _derivativeExpression;

        /// <summary>
        /// Returns the symbolic second derivative as a string.
        /// </summary>
        public string SecondDerivative => _secondDerivativeExpression;

        /// <summary>
        /// Approximates the domain by checking where the function is defined.
        /// </summary>
        public string GetDomainApproximation(double start = DefaultRangeStart, double end = DefaultRangeEnd, int numPoints = DefaultNumPoints)
        {
            var undefinedPoints = new List<double>();
            double step = (end - start) / numPoints;
            for (int i = 0; i <= numPoints; i++)
            {
                double x = start + i * step;
                try
                {
                    double val = _func(x);
                    if (double.IsNaN(val) || double.IsInfinity(val))
                        undefinedPoints.Add(x);
                }
                catch
                {
                    undefinedPoints.Add(x);
                }
            }

            if (undefinedPoints.Count == 0)
                return $"All real numbers (no issues detected in [{start}, {end}])";
            else
                return $"Potentially undefined near: {string.Join(", ", undefinedPoints.Take(10))} (further analysis required)";
        }

        /// <summary>
        /// Approximates the range over an interval.
        /// </summary>
        public (double Min, double Max) GetRange(double start = DefaultRangeStart, double end = DefaultRangeEnd, int numPoints = DefaultNumPoints)
        {
            double min = double.PositiveInfinity;
            double max = double.NegativeInfinity;
            double step = (end - start) / numPoints;
            for (int i = 0; i <= numPoints; i++)
            {
                double x = start + i * step;
                double val = _func(x);
                if (!double.IsNaN(val) && !double.IsInfinity(val))
                {
                    if (val < min) min = val;
                    if (val > max) max = val;
                }
            }
            return (min, max);
        }

        /// <summary>
        /// Finds zeros (roots) of the function within an interval using Brent's method.
        /// </summary>
        public List<double> FindZeros(double start = DefaultRangeStart, double end = DefaultRangeEnd, int numSubdivisions = 100)
        {
            var roots = new List<double>();
            double step = (end - start) / numSubdivisions;
            for (int i = 0; i < numSubdivisions; i++)
            {
                double a = start + i * step;
                double b = a + step;
                double fa = _func(a);
                double fb = _func(b);
                if (fa == 0) roots.Add(a);
                if (fb == 0) roots.Add(b);
                if (fa * fb < 0)
                {
                    double root = BrentRoot(a, b, 1e-10, 100);
                    if (!roots.Contains(Math.Round(root, 8)))
                        roots.Add(root);
                }
            }
            return roots.OrderBy(r => r).ToList();
        }

        /// <summary>
        /// Finds critical points (where first derivative = 0) within an interval.
        /// </summary>
        public List<double> FindCriticalPoints(double start = DefaultRangeStart, double end = DefaultRangeEnd, int numSubdivisions = 100)
        {
            return FindRootsOfDerivative(start, end, numSubdivisions);
        }

        /// <summary>
        /// Finds inflection points (where second derivative = 0) within an interval.
        /// </summary>
        public List<double> FindInflectionPoints(double start = DefaultRangeStart, double end = DefaultRangeEnd, int numSubdivisions = 100)
        {
            var inflectionPoints = new List<double>();
            double step = (end - start) / numSubdivisions;
            for (int i = 0; i < numSubdivisions; i++)
            {
                double a = start + i * step;
                double b = a + step;
                double fpa = _secondDerivativeFunc(a);
                double fpb = _secondDerivativeFunc(b);
                if (fpa == 0) inflectionPoints.Add(a);
                if (fpb == 0) inflectionPoints.Add(b);
                if (fpa * fpb < 0)
                {
                    double root = BrentRootForSecondDerivative(a, b, 1e-10, 100);
                    if (!inflectionPoints.Contains(Math.Round(root, 8)))
                        inflectionPoints.Add(root);
                }
            }
            return inflectionPoints.OrderBy(r => r).ToList();
        }

        private double BrentRoot(double a, double b, double tolerance, int maxIter)
        {
            double fa = _func(a);
            double fb = _func(b);
            if (fa == 0) return a;
            if (fb == 0) return b;
            if (fa * fb >= 0) throw new ArgumentException("Function must have opposite signs at endpoints.");

            double c = a, fc = fa, d = b - a, e = d;
            for (int iter = 0; iter < maxIter; iter++)
            {
                if (Math.Abs(fc) < Math.Abs(fb))
                {
                    a = b; b = c; c = a;
                    fa = fb; fb = fc; fc = fa;
                }
                double tol = tolerance * Math.Abs(b) + 1e-14;
                double m = 0.5 * (c - b);
                if (Math.Abs(m) <= tol || fb == 0) return b;
                if (Math.Abs(e) < tol || Math.Abs(fa) <= Math.Abs(fb))
                {
                    e = m; d = e;
                }
                else
                {
                    double s = fb / fa;
                    double p, q;
                    if (a == c)
                    {
                        p = 2 * m * s;
                        q = 1 - s;
                    }
                    else
                    {
                        double r = fb / fc;
                        double t = fa / fc;
                        p = s * (2 * m * t * (t - r) - (b - a) * (r - 1));
                        q = (t - 1) * (r - 1) * (s - 1);
                    }
                    if (p > 0) q = -q;
                    p = Math.Abs(p);
                    if (2 * p < Math.Min(3 * m * q - Math.Abs(tol * q), Math.Abs(e * q)))
                    {
                        e = d;
                        d = p / q;
                    }
                    else
                    {
                        e = m;
                        d = e;
                    }
                }
                a = b; fa = fb;
                if (Math.Abs(d) > tol) b += d;
                else b += (m > 0 ? tol : -tol);
                fb = _func(b);
                if ((fb > 0 && fc > 0) || (fb < 0 && fc < 0))
                {
                    c = a; fc = fa;
                    e = d = b - a;
                }
            }
            return b;
        }

        private double BrentRootForSecondDerivative(double a, double b, double tolerance, int maxIter)
        {
            double fa = _secondDerivativeFunc(a);
            double fb = _secondDerivativeFunc(b);
            if (fa == 0) return a;
            if (fb == 0) return b;
            if (fa * fb >= 0) throw new ArgumentException("Function must have opposite signs at endpoints.");

            double c = a, fc = fa, d = b - a, e = d;
            for (int iter = 0; iter < maxIter; iter++)
            {
                if (Math.Abs(fc) < Math.Abs(fb))
                {
                    a = b; b = c; c = a;
                    fa = fb; fb = fc; fc = fa;
                }
                double tol = tolerance * Math.Abs(b) + 1e-14;
                double m = 0.5 * (c - b);
                if (Math.Abs(m) <= tol || fb == 0) return b;
                if (Math.Abs(e) < tol || Math.Abs(fa) <= Math.Abs(fb))
                {
                    e = m; d = e;
                }
                else
                {
                    double s = fb / fa;
                    double p, q;
                    if (a == c)
                    {
                        p = 2 * m * s;
                        q = 1 - s;
                    }
                    else
                    {
                        double r = fb / fc;
                        double t = fa / fc;
                        p = s * (2 * m * t * (t - r) - (b - a) * (r - 1));
                        q = (t - 1) * (r - 1) * (s - 1);
                    }
                    if (p > 0) q = -q;
                    p = Math.Abs(p);
                    if (2 * p < Math.Min(3 * m * q - Math.Abs(tol * q), Math.Abs(e * q)))
                    {
                        e = d;
                        d = p / q;
                    }
                    else
                    {
                        e = m;
                        d = e;
                    }
                }
                a = b; fa = fb;
                if (Math.Abs(d) > tol) b += d;
                else b += (m > 0 ? tol : -tol);
                fb = _secondDerivativeFunc(b);
                if ((fb > 0 && fc > 0) || (fb < 0 && fc < 0))
                {
                    c = a; fc = fa;
                    e = d = b - a;
                }
            }
            return b;
        }

        private List<double> FindRootsOfDerivative(double start, double end, int numSubdivisions)
        {
            var roots = new List<double>();
            double step = (end - start) / numSubdivisions;
            for (int i = 0; i < numSubdivisions; i++)
            {
                double a = start + i * step;
                double b = a + step;
                double fa = _derivativeFunc(a);
                double fb = _derivativeFunc(b);
                if (fa == 0) roots.Add(a);
                if (fb == 0) roots.Add(b);
                if (fa * fb < 0)
                {
                    double root = BrentRootForDerivative(a, b, 1e-10, 100);
                    if (!roots.Contains(Math.Round(root, 8)))
                        roots.Add(root);
                }
            }
            return roots.OrderBy(r => r).ToList();
        }

        private double BrentRootForDerivative(double a, double b, double tolerance, int maxIter)
        {
            double fa = _derivativeFunc(a);
            double fb = _derivativeFunc(b);
            if (fa == 0) return a;
            if (fb == 0) return b;
            if (fa * fb >= 0) throw new ArgumentException("Function must have opposite signs at endpoints.");

            double c = a, fc = fa, d = b - a, e = d;
            for (int iter = 0; iter < maxIter; iter++)
            {
                if (Math.Abs(fc) < Math.Abs(fb))
                {
                    a = b; b = c; c = a;
                    fa = fb; fb = fc; fc = fa;
                }
                double tol = tolerance * Math.Abs(b) + 1e-14;
                double m = 0.5 * (c - b);
                if (Math.Abs(m) <= tol || fb == 0) return b;
                if (Math.Abs(e) < tol || Math.Abs(fa) <= Math.Abs(fb))
                {
                    e = m; d = e;
                }
                else
                {
                    double s = fb / fa;
                    double p, q;
                    if (a == c)
                    {
                        p = 2 * m * s;
                        q = 1 - s;
                    }
                    else
                    {
                        double r = fb / fc;
                        double t = fa / fc;
                        p = s * (2 * m * t * (t - r) - (b - a) * (r - 1));
                        q = (t - 1) * (r - 1) * (s - 1);
                    }
                    if (p > 0) q = -q;
                    p = Math.Abs(p);
                    if (2 * p < Math.Min(3 * m * q - Math.Abs(tol * q), Math.Abs(e * q)))
                    {
                        e = d;
                        d = p / q;
                    }
                    else
                    {
                        e = m;
                        d = e;
                    }
                }
                a = b; fa = fb;
                if (Math.Abs(d) > tol) b += d;
                else b += (m > 0 ? tol : -tol);
                fb = _derivativeFunc(b);
                if ((fb > 0 && fc > 0) || (fb < 0 && fc < 0))
                {
                    c = a; fc = fa;
                    e = d = b - a;
                }
            }
            return b;
        }

        /// <summary>
        /// Prints all properties to the console.
        /// </summary>
        public void PrintProperties(double start = DefaultRangeStart, double end = DefaultRangeEnd)
        {
            Console.WriteLine($"Function: f(x) = {_originalExpression}");
            Console.WriteLine($"Derivative: f'(x) = {_derivativeExpression}");
            Console.WriteLine($"Second derivative: f''(x) = {_secondDerivativeExpression}");
            Console.WriteLine($"Domain (approximate): {GetDomainApproximation(start, end)}");
            var range = GetRange(start, end);
            Console.WriteLine($"Range (approx on [{start}, {end}]): [{range.Min:F6}, {range.Max:F6}]");
            
            var zeros = FindZeros(start, end);
            Console.WriteLine($"Zeros (roots): {(zeros.Count == 0 ? "none found" : string.Join(", ", zeros.Select(z => z.ToString("F6"))))}");
            
            var critical = FindCriticalPoints(start, end);
            Console.WriteLine($"Critical points (f' = 0): {(critical.Count == 0 ? "none found" : string.Join(", ", critical.Select(c => c.ToString("F6"))))}");
            
            var inflection = FindInflectionPoints(start, end);
            Console.WriteLine($"Inflection points (f'' = 0): {(inflection.Count == 0 ? "none found" : string.Join(", ", inflection.Select(i => i.ToString("F6"))))}");
        }
    }

    // ---------- Expression Parser ----------
    internal abstract class ExpressionNode
    {
        public abstract double Evaluate(double x);
        public abstract Expression<Func<double, double>> ToLambda();
        public Func<double, double> Compile() => ToLambda().Compile();
        public abstract string ToString();
    }

    internal class ConstantNode : ExpressionNode
    {
        public double Value { get; }
        public ConstantNode(double value) => Value = value;
        public override double Evaluate(double x) => Value;
        public override Expression<Func<double, double>> ToLambda() => (x) => Value;
        public override string ToString() => Value.ToString();
    }

    internal class VariableNode : ExpressionNode
    {
        public override double Evaluate(double x) => x;
        public override Expression<Func<double, double>> ToLambda() => (x) => x;
        public override string ToString() => "x";
    }

    internal class BinaryOpNode : ExpressionNode
    {
        public enum OpType { Add, Subtract, Multiply, Divide, Power }
        public OpType Op { get; }
        public ExpressionNode Left { get; }
        public ExpressionNode Right { get; }
        public BinaryOpNode(OpType op, ExpressionNode left, ExpressionNode right)
        {
            Op = op;
            Left = left;
            Right = right;
        }
        public override double Evaluate(double x)
        {
            double l = Left.Evaluate(x);
            double r = Right.Evaluate(x);
            return Op switch
            {
                OpType.Add => l + r,
                OpType.Subtract => l - r,
                OpType.Multiply => l * r,
                OpType.Divide => l / r,
                OpType.Power => Math.Pow(l, r),
                _ => throw new InvalidOperationException()
            };
        }
        public override Expression<Func<double, double>> ToLambda()
        {
            var leftExpr = Left.ToLambda();
            var rightExpr = Right.ToLambda();
            return Op switch
            {
                OpType.Add => (x) => leftExpr.Compile()(x) + rightExpr.Compile()(x),
                OpType.Subtract => (x) => leftExpr.Compile()(x) - rightExpr.Compile()(x),
                OpType.Multiply => (x) => leftExpr.Compile()(x) * rightExpr.Compile()(x),
                OpType.Divide => (x) => leftExpr.Compile()(x) / rightExpr.Compile()(x),
                OpType.Power => (x) => Math.Pow(leftExpr.Compile()(x), rightExpr.Compile()(x)),
                _ => throw new InvalidOperationException()
            };
        }
        public override string ToString()
        {
            string opStr = Op switch
            {
                OpType.Add => "+",
                OpType.Subtract => "-",
                OpType.Multiply => "*",
                OpType.Divide => "/",
                OpType.Power => "^",
                _ => "?"
            };
            return $"({Left} {opStr} {Right})";
        }
    }

    internal class UnaryFuncNode : ExpressionNode
    {
        public enum FuncType { Sin, Cos, Tan, Asin, Acos, Atan, Sinh, Cosh, Tanh, Exp, Log, Log10, Sqrt, Abs }
        public FuncType Func { get; }
        public ExpressionNode Arg { get; }
        public UnaryFuncNode(FuncType func, ExpressionNode arg)
        {
            Func = func;
            Arg = arg;
        }
        public override double Evaluate(double x)
        {
            double a = Arg.Evaluate(x);
            return Func switch
            {
                FuncType.Sin => Math.Sin(a),
                FuncType.Cos => Math.Cos(a),
                FuncType.Tan => Math.Tan(a),
                FuncType.Asin => Math.Asin(a),
                FuncType.Acos => Math.Acos(a),
                FuncType.Atan => Math.Atan(a),
                FuncType.Sinh => Math.Sinh(a),
                FuncType.Cosh => Math.Cosh(a),
                FuncType.Tanh => Math.Tanh(a),
                FuncType.Exp => Math.Exp(a),
                FuncType.Log => Math.Log(a),
                FuncType.Log10 => Math.Log10(a),
                FuncType.Sqrt => Math.Sqrt(a),
                FuncType.Abs => Math.Abs(a),
                _ => throw new InvalidOperationException()
            };
        }
        public override Expression<Func<double, double>> ToLambda()
        {
            var argExpr = Arg.ToLambda();
            return Func switch
            {
                FuncType.Sin => (x) => Math.Sin(argExpr.Compile()(x)),
                FuncType.Cos => (x) => Math.Cos(argExpr.Compile()(x)),
                FuncType.Tan => (x) => Math.Tan(argExpr.Compile()(x)),
                FuncType.Asin => (x) => Math.Asin(argExpr.Compile()(x)),
                FuncType.Acos => (x) => Math.Acos(argExpr.Compile()(x)),
                FuncType.Atan => (x) => Math.Atan(argExpr.Compile()(x)),
                FuncType.Sinh => (x) => Math.Sinh(argExpr.Compile()(x)),
                FuncType.Cosh => (x) => Math.Cosh(argExpr.Compile()(x)),
                FuncType.Tanh => (x) => Math.Tanh(argExpr.Compile()(x)),
                FuncType.Exp => (x) => Math.Exp(argExpr.Compile()(x)),
                FuncType.Log => (x) => Math.Log(argExpr.Compile()(x)),
                FuncType.Log10 => (x) => Math.Log10(argExpr.Compile()(x)),
                FuncType.Sqrt => (x) => Math.Sqrt(argExpr.Compile()(x)),
                FuncType.Abs => (x) => Math.Abs(argExpr.Compile()(x)),
                _ => throw new InvalidOperationException()
            };
        }
        public override string ToString()
        {
            string name = Func switch
            {
                FuncType.Sin => "sin",
                FuncType.Cos => "cos",
                FuncType.Tan => "tan",
                FuncType.Asin => "asin",
                FuncType.Acos => "acos",
                FuncType.Atan => "atan",
                FuncType.Sinh => "sinh",
                FuncType.Cosh => "cosh",
                FuncType.Tanh => "tanh",
                FuncType.Exp => "exp",
                FuncType.Log => "log",
                FuncType.Log10 => "log10",
                FuncType.Sqrt => "sqrt",
                FuncType.Abs => "abs",
                _ => "?"
            };
            return $"{name}({Arg})";
        }
    }

    internal static class Parser
    {
        private static int _pos;
        private static string _input;

        public static ExpressionNode Parse(string expression)
        {
            _input = expression.Replace(" ", "");
            _pos = 0;
            var node = ParseExpression();
            if (_pos < _input.Length)
                throw new ArgumentException($"Unexpected character at position {_pos}: {_input[_pos]}");
            return node;
        }

        private static ExpressionNode ParseExpression()
        {
            var left = ParseTerm();
            while (_pos < _input.Length)
            {
                char op = _input[_pos];
                if (op == '+')
                {
                    _pos++;
                    left = new BinaryOpNode(BinaryOpNode.OpType.Add, left, ParseTerm());
                }
                else if (op == '-')
                {
                    _pos++;
                    left = new BinaryOpNode(BinaryOpNode.OpType.Subtract, left, ParseTerm());
                }
                else
                    break;
            }
            return left;
        }

        private static ExpressionNode ParseTerm()
        {
            var left = ParseFactor();
            while (_pos < _input.Length)
            {
                char op = _input[_pos];
                if (op == '*')
                {
                    _pos++;
                    left = new BinaryOpNode(BinaryOpNode.OpType.Multiply, left, ParseFactor());
                }
                else if (op == '/')
                {
                    _pos++;
                    left = new BinaryOpNode(BinaryOpNode.OpType.Divide, left, ParseFactor());
                }
                else
                    break;
            }
            return left;
        }

        private static ExpressionNode ParseFactor()
        {
            var node = ParsePower();
            while (_pos < _input.Length && _input[_pos] == '^')
            {
                _pos++;
                node = new BinaryOpNode(BinaryOpNode.OpType.Power, node, ParsePower());
            }
            return node;
        }

        private static ExpressionNode ParsePower()
        {
            if (_pos >= _input.Length) throw new ArgumentException("Unexpected end of expression");

            char c = _input[_pos];
            if (c == '(')
            {
                _pos++;
                var node = ParseExpression();
                if (_pos >= _input.Length || _input[_pos] != ')')
                    throw new ArgumentException("Missing closing parenthesis");
                _pos++;
                return node;
            }
            else if (char.IsDigit(c) || c == '.')
            {
                int start = _pos;
                while (_pos < _input.Length && (char.IsDigit(_input[_pos]) || _input[_pos] == '.'))
                    _pos++;
                string numStr = _input.Substring(start, _pos - start);
                if (!double.TryParse(numStr, out double value))
                    throw new ArgumentException($"Invalid number: {numStr}");
                return new ConstantNode(value);
            }
            else if (c == 'x')
            {
                _pos++;
                return new VariableNode();
            }
            else if (char.IsLetter(c))
            {
                int start = _pos;
                while (_pos < _input.Length && char.IsLetter(_input[_pos]))
                    _pos++;
                string funcName = _input.Substring(start, _pos - start);
                if (_pos >= _input.Length || _input[_pos] != '(')
                    throw new ArgumentException($"Expected '(' after function '{funcName}'");
                _pos++; // skip '('
                var arg = ParseExpression();
                if (_pos >= _input.Length || _input[_pos] != ')')
                    throw new ArgumentException($"Missing closing parenthesis after argument of '{funcName}'");
                _pos++;
                var funcType = funcName.ToLower() switch
                {
                    "sin" => UnaryFuncNode.FuncType.Sin,
                    "cos" => UnaryFuncNode.FuncType.Cos,
                    "tan" => UnaryFuncNode.FuncType.Tan,
                    "asin" => UnaryFuncNode.FuncType.Asin,
                    "acos" => UnaryFuncNode.FuncType.Acos,
                    "atan" => UnaryFuncNode.FuncType.Atan,
                    "sinh" => UnaryFuncNode.FuncType.Sinh,
                    "cosh" => UnaryFuncNode.FuncType.Cosh,
                    "tanh" => UnaryFuncNode.FuncType.Tanh,
                    "exp" => UnaryFuncNode.FuncType.Exp,
                    "log" => UnaryFuncNode.FuncType.Log,
                    "log10" => UnaryFuncNode.FuncType.Log10,
                    "sqrt" => UnaryFuncNode.FuncType.Sqrt,
                    "abs" => UnaryFuncNode.FuncType.Abs,
                    _ => throw new ArgumentException($"Unknown function: {funcName}")
                };
                return new UnaryFuncNode(funcType, arg);
            }
            else
                throw new ArgumentException($"Unexpected character: {c}");
        }
    }

    // ---------- Symbolic Differentiator ----------
    internal static class Differentiator
    {
        public static ExpressionNode Differentiate(ExpressionNode node)
        {
            return node switch
            {
                ConstantNode _ => new ConstantNode(0),
                VariableNode _ => new ConstantNode(1),
                BinaryOpNode bin => bin.Op switch
                {
                    BinaryOpNode.OpType.Add => new BinaryOpNode(BinaryOpNode.OpType.Add, Differentiate(bin.Left), Differentiate(bin.Right)),
                    BinaryOpNode.OpType.Subtract => new BinaryOpNode(BinaryOpNode.OpType.Subtract, Differentiate(bin.Left), Differentiate(bin.Right)),
                    BinaryOpNode.OpType.Multiply => new BinaryOpNode(BinaryOpNode.OpType.Add,
                        new BinaryOpNode(BinaryOpNode.OpType.Multiply, Differentiate(bin.Left), bin.Right),
                        new BinaryOpNode(BinaryOpNode.OpType.Multiply, bin.Left, Differentiate(bin.Right))),
                    BinaryOpNode.OpType.Divide => new BinaryOpNode(BinaryOpNode.OpType.Divide,
                        new BinaryOpNode(BinaryOpNode.OpType.Subtract,
                            new BinaryOpNode(BinaryOpNode.OpType.Multiply, Differentiate(bin.Left), bin.Right),
                            new BinaryOpNode(BinaryOpNode.OpType.Multiply, bin.Left, Differentiate(bin.Right))),
                        new BinaryOpNode(BinaryOpNode.OpType.Power, bin.Right, new ConstantNode(2))),
                    BinaryOpNode.OpType.Power => DifferentiatePower(bin),
                    _ => throw new InvalidOperationException()
                },
                UnaryFuncNode unary => DifferentiateUnary(unary),
                _ => throw new ArgumentException("Unknown node type")
            };
        }

        private static ExpressionNode DifferentiatePower(BinaryOpNode power)
        {
            // d/dx (u^v) = u^v * (v' * ln(u) + v * u'/u)
            var u = power.Left;
            var v = power.Right;
            var du = Differentiate(u);
            var dv = Differentiate(v);
            var uPowV = new BinaryOpNode(BinaryOpNode.OpType.Power, u, v);
            var term1 = new BinaryOpNode(BinaryOpNode.OpType.Multiply, dv, new UnaryFuncNode(UnaryFuncNode.FuncType.Log, u));
            var term2 = new BinaryOpNode(BinaryOpNode.OpType.Multiply, v, new BinaryOpNode(BinaryOpNode.OpType.Divide, du, u));
            var sum = new BinaryOpNode(BinaryOpNode.OpType.Add, term1, term2);
            return new BinaryOpNode(BinaryOpNode.OpType.Multiply, uPowV, sum);
        }

        private static ExpressionNode DifferentiateUnary(UnaryFuncNode unary)
        {
            var arg = unary.Arg;
            var dArg = Differentiate(arg);
            ExpressionNode deriv = unary.Func switch
            {
                UnaryFuncNode.FuncType.Sin => new UnaryFuncNode(UnaryFuncNode.FuncType.Cos, arg),
                UnaryFuncNode.FuncType.Cos => new UnaryFuncNode(UnaryFuncNode.FuncType.Sin, new UnaryFuncNode(UnaryFuncNode.FuncType.Negate, arg)), // -sin
                UnaryFuncNode.FuncType.Tan => new BinaryOpNode(BinaryOpNode.OpType.Power, new UnaryFuncNode(UnaryFuncNode.FuncType.Cos, arg), new ConstantNode(-2)),
                UnaryFuncNode.FuncType.Asin => new BinaryOpNode(BinaryOpNode.OpType.Divide, new ConstantNode(1),
                    new UnaryFuncNode(UnaryFuncNode.FuncType.Sqrt, new BinaryOpNode(BinaryOpNode.OpType.Subtract, new ConstantNode(1), new BinaryOpNode(BinaryOpNode.OpType.Power, arg, new ConstantNode(2))))),
                UnaryFuncNode.FuncType.Acos => new BinaryOpNode(BinaryOpNode.OpType.Divide, new ConstantNode(-1),
                    new UnaryFuncNode(UnaryFuncNode.FuncType.Sqrt, new BinaryOpNode(BinaryOpNode.OpType.Subtract, new ConstantNode(1), new BinaryOpNode(BinaryOpNode.OpType.Power, arg, new ConstantNode(2))))),
                UnaryFuncNode.FuncType.Atan => new BinaryOpNode(BinaryOpNode.OpType.Divide, new ConstantNode(1),
                    new BinaryOpNode(BinaryOpNode.OpType.Add, new ConstantNode(1), new BinaryOpNode(BinaryOpNode.OpType.Power, arg, new ConstantNode(2)))),
                UnaryFuncNode.FuncType.Sinh => new UnaryFuncNode(UnaryFuncNode.FuncType.Cosh, arg),
                UnaryFuncNode.FuncType.Cosh => new UnaryFuncNode(UnaryFuncNode.FuncType.Sinh, arg),
                UnaryFuncNode.FuncType.Tanh => new BinaryOpNode(BinaryOpNode.OpType.Power, new UnaryFuncNode(UnaryFuncNode.FuncType.Cosh, arg), new ConstantNode(-2)),
                UnaryFuncNode.FuncType.Exp => unary,
                UnaryFuncNode.FuncType.Log => new BinaryOpNode(BinaryOpNode.OpType.Divide, new ConstantNode(1), arg),
                UnaryFuncNode.FuncType.Log10 => new BinaryOpNode(BinaryOpNode.OpType.Divide, new ConstantNode(1),
                    new BinaryOpNode(BinaryOpNode.OpType.Multiply, arg, new ConstantNode(Math.Log(10)))),
                UnaryFuncNode.FuncType.Sqrt => new BinaryOpNode(BinaryOpNode.OpType.Divide, new ConstantNode(1),
                    new BinaryOpNode(BinaryOpNode.OpType.Multiply, new ConstantNode(2), new UnaryFuncNode(UnaryFuncNode.FuncType.Sqrt, arg))),
                UnaryFuncNode.FuncType.Abs => new BinaryOpNode(BinaryOpNode.OpType.Divide, arg,
                    new UnaryFuncNode(UnaryFuncNode.FuncType.Abs, arg)), // sign(x)
                _ => throw new InvalidOperationException()
            };
            // For negation we don't have a node, so we treat -sin as multiply by -1
            if (unary.Func == UnaryFuncNode.FuncType.Cos)
            {
                // deriv = -sin(arg) * dArg
                var negSin = new BinaryOpNode(BinaryOpNode.OpType.Multiply, new ConstantNode(-1), deriv);
                return new BinaryOpNode(BinaryOpNode.OpType.Multiply, negSin, dArg);
            }
            return new BinaryOpNode(BinaryOpNode.OpType.Multiply, deriv, dArg);
        }
    }

    // Helper node for negation (used only internally)
    internal class NegateNode : UnaryFuncNode
    {
        public NegateNode(ExpressionNode arg) : base(UnaryFuncNode.FuncType.Abs, arg) { } // HACK: not used
    }

    // Add Negate to FuncType for completeness
    internal partial class UnaryFuncNode
    {
        public enum FuncType { Sin, Cos, Tan, Asin, Acos, Atan, Sinh, Cosh, Tanh, Exp, Log, Log10, Sqrt, Abs, Negate }
    }

    // Update parser to handle unary minus? Not needed for differentiation.
    // Fix Negate handling in differentiator (simplify)
    static class DifferentiatorExtensions
    {
        public static ExpressionNode Negate(this ExpressionNode node) =>
            new BinaryOpNode(BinaryOpNode.OpType.Multiply, new ConstantNode(-1), node);
    }

    // ---------- Main Program ----------
    public class Program
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("Mathematical Function Analyzer");
            Console.WriteLine("Enter a function of x (e.g., 'x^2 + sin(x)' or 'exp(x)*cos(x)'):");
            string input = Console.ReadLine();
            if (string.IsNullOrWhiteSpace(input))
            {
                Console.WriteLine("No input provided. Using default: x^3 - 3*x");
                input = "x^3 - 3*x";
            }

            try
            {
                var analyzer = new FunctionAnalyzer(input);
                analyzer.PrintProperties(-5, 5);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
            }

            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }
    }
}