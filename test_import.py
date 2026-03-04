try:
    from auto_nesting import AutoNester
    print("Import success")
except ImportError as e:
    print(f"Import failed: {e}")
