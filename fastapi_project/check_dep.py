try:
    import markupsafe
    from markupsafe import Markup
    print("MarkupSafe is installed and working.")
except ImportError as e:
    print(f"MarkupSafe is MISSING: {e}")
