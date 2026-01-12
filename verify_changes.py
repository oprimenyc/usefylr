import sys
import os

# Add current directory to path so imports work
current_dir = os.getcwd()
sys.path.append(current_dir)

print(f"Checking imports from {current_dir}")

def check_import(module_name, item_name=None):
    try:
        if item_name:
            exec(f"from {module_name} import {item_name}")
            print(f"[OK] {module_name}.{item_name} imported successfully")
        else:
            exec(f"import {module_name}")
            print(f"[OK] {module_name} imported successfully")
        return True
    except Exception as e:
        import traceback
        print(f"[FAIL] {module_name} failed: {e}")
        traceback.print_exc()
        return False

# Check dependencies
# app.models is correct
check_import("app.models", "Form1099")

# modules are at root level
check_import("modules.pdf_utils", "generate_tax_form_pdf")
check_import("modules.contractor_routes")
check_import("modules.smart_ledger", "SmartLedger")
