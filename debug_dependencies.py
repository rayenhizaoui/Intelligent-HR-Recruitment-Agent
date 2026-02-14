import sys
import importlib

packages = [
    "numpy",
    "sklearn",
    "scipy",
    "torch",
    "transformers",
    "sentence_transformers",
    "chromadb"
]

print(f"Python: {sys.version}")

for package in packages:
    try:
        module = importlib.import_module(package)
        version = getattr(module, "__version__", "unknown")
        print(f"✅ {package}: {version}")
    except Exception as e:
        print(f"❌ {package}: FAILED - {e}")
        # Dig deeper for specific sub-errors if possible
        if package == "sentence_transformers":
            try:
                import sentence_transformers
            except ImportError as ie:
                print(f"   ImportError Traceback: {ie}")
            except Exception as ex:
                print(f"   Exception Traceback: {ex}")
