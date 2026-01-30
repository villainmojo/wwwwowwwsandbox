"""
Console Calculator - ast 기반 안전한 수식 파서
Windows exe 배포용 단일 파일 구조
"""

import ast
import operator
from typing import Union

# 지원하는 연산자 매핑
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_eval(node: ast.AST) -> Union[int, float]:
    """AST 노드를 재귀적으로 평가"""
    
    # 숫자 리터럴
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"지원하지 않는 값: {node.value}")
    
    # 이항 연산 (a + b, a * b 등)
    if isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        op_type = type(node.op)
        
        if op_type not in OPERATORS:
            raise ValueError(f"지원하지 않는 연산자: {op_type.__name__}")
        
        # 0으로 나누기 체크
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("0으로 나눌 수 없습니다")
        
        return OPERATORS[op_type](left, right)
    
    # 단항 연산 (+a, -a)
    if isinstance(node, ast.UnaryOp):
        operand = safe_eval(node.operand)
        op_type = type(node.op)
        
        if op_type not in OPERATORS:
            raise ValueError(f"지원하지 않는 연산자: {op_type.__name__}")
        
        return OPERATORS[op_type](operand)
    
    # 괄호로 묶인 표현식
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    
    raise ValueError(f"지원하지 않는 구문: {type(node).__name__}")


def calculate(expression: str) -> Union[int, float]:
    """수식 문자열을 계산"""
    # 공백 제거 및 정리
    expression = expression.strip()
    
    if not expression:
        raise ValueError("수식을 입력해주세요")
    
    # AST로 파싱
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as e:
        raise ValueError(f"잘못된 수식: {e.msg}")
    
    # 안전하게 평가
    result = safe_eval(tree)
    
    # 정수로 표현 가능하면 정수로
    if isinstance(result, float) and result.is_integer():
        return int(result)
    
    return result


def print_banner():
    """시작 배너 출력"""
    print("=" * 40)
    print("       Console Calculator")
    print("=" * 40)
    print("  지원: +, -, *, /, //, %, ** (거듭제곱)")
    print("  괄호 사용 가능: (1 + 2) * 3")
    print("  종료: exit 또는 quit")
    print("=" * 40)
    print()


def main():
    """메인 루프"""
    print_banner()
    
    while True:
        try:
            # 입력 받기
            user_input = input(">>> ").strip()
            
            # 종료 명령 체크
            if user_input.lower() in ('exit', 'quit', 'q'):
                print("계산기를 종료합니다. 안녕히 가세요!")
                break
            
            # 빈 입력 무시
            if not user_input:
                continue
            
            # 계산 및 결과 출력
            result = calculate(user_input)
            print(f"= {result}")
            
        except ZeroDivisionError as e:
            print(f"[오류] {e}")
        except ValueError as e:
            print(f"[오류] {e}")
        except KeyboardInterrupt:
            print("\n계산기를 종료합니다. 안녕히 가세요!")
            break
        except Exception as e:
            print(f"[오류] 예상치 못한 오류: {e}")
    
    # exe 실행 시 창이 바로 닫히지 않도록
    input("\nEnter를 누르면 종료됩니다...")


if __name__ == "__main__":
    main()
