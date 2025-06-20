import ast
import math
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation
from ..core.config import settings


class FormulaSecurityError(Exception):
    """Raised when a formula contains unsafe operations"""
    pass


class FormulaEvaluationError(Exception):
    """Raised when a formula fails to evaluate"""
    pass


class FormulaEngine:
    """Secure formula evaluation engine for financial calculations"""
    
    def __init__(self):
        self.allowed_functions = {
            # Math functions
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pow': pow,
            'sqrt': math.sqrt,
            'ceil': math.ceil,
            'floor': math.floor,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            
            # Financial functions
            'pmt': self._pmt,  # Payment calculation
            'fv': self._fv,    # Future value
            'pv': self._pv,    # Present value
            'rate': self._rate, # Interest rate
            'nper': self._nper, # Number of periods
        }
        
        self.allowed_constants = {
            'pi': math.pi,
            'e': math.e,
        }
    
    def validate_formula(self, formula: str) -> bool:
        """Validate that a formula is safe to evaluate"""
        try:
            # Check length
            if len(formula) > settings.MAX_FORMULA_LENGTH:
                raise FormulaSecurityError(f"Formula too long (max {settings.MAX_FORMULA_LENGTH} characters)")
            
            # Parse the formula
            tree = ast.parse(formula, mode='eval')
            
            # Check for unsafe operations
            self._check_node_safety(tree.body)
            
            return True
            
        except SyntaxError as e:
            raise FormulaSecurityError(f"Invalid formula syntax: {e}")
        except Exception as e:
            raise FormulaSecurityError(f"Formula validation failed: {e}")
    
    def _check_node_safety(self, node: ast.AST) -> None:
        """Recursively check if an AST node contains only safe operations"""
        if isinstance(node, ast.Expression):
            self._check_node_safety(node.body)
        elif isinstance(node, ast.Name):
            # Only allow variables (will be provided in context)
            pass
        elif isinstance(node, ast.Constant):
            # Allow all constants
            pass
        elif isinstance(node, ast.BinOp):
            # Allow basic math operations
            if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
                raise FormulaSecurityError(f"Unsafe binary operation: {type(node.op).__name__}")
            self._check_node_safety(node.left)
            self._check_node_safety(node.right)
        elif isinstance(node, ast.UnaryOp):
            # Allow unary operations
            if not isinstance(node.op, (ast.UAdd, ast.USub)):
                raise FormulaSecurityError(f"Unsafe unary operation: {type(node.op).__name__}")
            self._check_node_safety(node.operand)
        elif isinstance(node, ast.Call):
            # Check function calls
            if not isinstance(node.func, ast.Name):
                raise FormulaSecurityError("Function calls must use simple names")
            
            func_name = node.func.id
            if func_name not in self.allowed_functions:
                raise FormulaSecurityError(f"Function '{func_name}' is not allowed")
            
            # Check arguments
            for arg in node.args:
                self._check_node_safety(arg)
        elif isinstance(node, ast.Compare):
            # Allow comparisons
            self._check_node_safety(node.left)
            for comparator in node.comparators:
                self._check_node_safety(comparator)
        elif isinstance(node, ast.IfExp):
            # Allow conditional expressions
            self._check_node_safety(node.test)
            self._check_node_safety(node.body)
            self._check_node_safety(node.orelse)
        else:
            raise FormulaSecurityError(f"Unsafe operation: {type(node).__name__}")
    
    def evaluate_formula(self, formula: str, variables: Dict[str, Any]) -> Decimal:
        """Safely evaluate a formula with given variables"""
        try:
            # Validate the formula first
            self.validate_formula(formula)
            
            # Create safe globals
            safe_globals = {
                **self.allowed_functions,
                **self.allowed_constants,
                **variables,
                '__builtins__': {}  # Disable builtins
            }
            
            # Evaluate the formula
            result = eval(formula, safe_globals, {})
            
            # Convert to Decimal for financial precision
            if isinstance(result, (int, float)):
                return Decimal(str(result))
            elif isinstance(result, Decimal):
                return result
            else:
                raise FormulaEvaluationError(f"Formula must return a number, got {type(result).__name__}")
                
        except ZeroDivisionError:
            raise FormulaEvaluationError("Division by zero")
        except (ValueError, TypeError) as e:
            raise FormulaEvaluationError(f"Formula evaluation error: {e}")
        except Exception as e:
            raise FormulaEvaluationError(f"Unexpected error: {e}")
    
    def test_formula(self, formula: str, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Test a formula with multiple test cases"""
        results = []
        
        for i, test_case in enumerate(test_cases):
            try:
                result = self.evaluate_formula(formula, test_case['variables'])
                results.append({
                    'case': i + 1,
                    'variables': test_case['variables'],
                    'result': result,
                    'error': None
                })
            except Exception as e:
                results.append({
                    'case': i + 1,
                    'variables': test_case['variables'],
                    'result': None,
                    'error': str(e)
                })
        
        return results
    
    # Financial calculation helper functions
    def _pmt(self, rate: float, nper: int, pv: float, fv: float = 0, when: int = 0) -> float:
        """Calculate payment for a loan"""
        if rate == 0:
            return -(pv + fv) / nper
        
        rate_per_period = rate / 12  # Assuming monthly payments
        return -((pv * (1 + rate_per_period) ** nper) + fv) / (((1 + rate_per_period) ** nper - 1) / rate_per_period)
    
    def _fv(self, rate: float, nper: int, pmt: float, pv: float = 0, when: int = 0) -> float:
        """Calculate future value"""
        rate_per_period = rate / 12
        return pv * (1 + rate_per_period) ** nper + pmt * (((1 + rate_per_period) ** nper - 1) / rate_per_period)
    
    def _pv(self, rate: float, nper: int, pmt: float, fv: float = 0, when: int = 0) -> float:
        """Calculate present value"""
        rate_per_period = rate / 12
        return (fv + pmt * (((1 + rate_per_period) ** nper - 1) / rate_per_period)) / (1 + rate_per_period) ** nper
    
    def _rate(self, nper: int, pmt: float, pv: float, fv: float = 0, when: int = 0, guess: float = 0.1) -> float:
        """Calculate interest rate (simplified)"""
        # This is a simplified implementation
        # In practice, you might want to use a more sophisticated numerical method
        return 0.05  # Placeholder
    
    def _nper(self, rate: float, pmt: float, pv: float, fv: float = 0, when: int = 0) -> float:
        """Calculate number of periods"""
        if rate == 0:
            return -(pv + fv) / pmt
        
        rate_per_period = rate / 12
        return math.log((pmt - fv * rate_per_period) / (pmt + pv * rate_per_period)) / math.log(1 + rate_per_period)


# Global instance
formula_engine = FormulaEngine() 