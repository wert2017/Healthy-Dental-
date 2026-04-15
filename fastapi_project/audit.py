import ast
import sys

def check_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    issues = []

    for node in ast.walk(tree):
        # Find endpoint functions
        if isinstance(node, ast.FunctionDef):
            is_endpoint = any(isinstance(d, ast.Call) and getattr(d.func, "attr", "") in ["get", "post", "put", "delete"] for d in node.decorator_list)
            
            # Check if it has try/except with rollback
            has_commit = False
            has_rollback = False
            for child in ast.walk(node):
                if isinstance(child, ast.Attribute) and child.attr == "commit":
                    has_commit = True
                if isinstance(child, ast.Attribute) and child.attr == "rollback":
                    has_rollback = True
            
            if has_commit and not has_rollback:
                issues.append(f"Function {node.name} has session.commit() but no session.rollback(). Risk of stuck transactions.")

    return issues

if __name__ == "__main__":
    issues = check_file("c:/HD/fastapi_project/main.py")
    for issue in issues:
        print(issue)
    if not issues:
        print("No immediate missing rollback issues found.")
