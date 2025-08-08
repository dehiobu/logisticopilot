#!/usr/bin/env python3
# ==============================================================================
# 🔍 Dependency Checker for LogiBot AI Copilot
# ==============================================================================

import sys
import importlib
import subprocess
from typing import Dict, List, Tuple
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Required packages for LogiBot
REQUIRED_PACKAGES = {
    # Core framework
    'streamlit': 'Web application framework',
    'pandas': 'Data manipulation and analysis',
    'numpy': 'Numerical computing',
    
    # Excel handling
    'openpyxl': 'Excel file reading/writing',
    'xlsxwriter': 'Excel file writing',
    
    # LLM and AI
    'langchain': 'LLM orchestration framework',
    'langchain_openai': 'OpenAI integration for LangChain',
    'langchain_community': 'Community integrations for LangChain',
    'openai': 'OpenAI API client',
    'tiktoken': 'OpenAI tokenizer',
    
    # Vector database
    'faiss': 'Vector similarity search (CPU version)',
    
    # Data validation
    'pydantic': 'Data validation and parsing',
    
    # Visualization and mapping
    'plotly': 'Interactive plotting',
    'folium': 'Interactive maps',
    'streamlit_folium': 'Folium integration for Streamlit',
    'matplotlib': 'Static plotting',
    'seaborn': 'Statistical visualization',
    
    # PDF and reporting
    'reportlab': 'PDF generation',
    'fpdf': 'Simple PDF generation',
    
    # Utilities
    'jinja2': 'Template engine',
    'requests': 'HTTP client',
    'python_dateutil': 'Date/time utilities',
    'dotenv': 'Environment variable management',
}

# Optional packages
OPTIONAL_PACKAGES = {
    'loguru': 'Enhanced logging',
    'pytest': 'Testing framework',
    'black': 'Code formatting',
    'flake8': 'Code linting',
}

def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """
    Check if a package is installed and importable.
    
    Args:
        package_name: Name of the package
        import_name: Name to use for importing (if different from package_name)
    
    Returns:
        Tuple of (is_installed, version_or_error)
    """
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'Unknown version')
        return True, version
    except ImportError as e:
        return False, str(e)

def get_pip_version(package_name: str) -> str:
    """Get package version from pip list."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()
        return "Not found"
    except Exception:
        return "Unknown"

def print_header():
    """Print a nice header."""
    print("=" * 70)
    print("🔍 LogiBot AI Copilot - Dependency Check")
    print("=" * 70)

def print_section(title: str):
    """Print a section header."""
    print(f"\n📦 {title}")
    print("-" * 50)

def check_python_version():
    """Check Python version."""
    print_section("Python Version")
    version = sys.version.split()[0]
    major, minor = map(int, version.split('.')[:2])
    
    if major >= 3 and minor >= 8:
        print(f"✅ Python {version} (Compatible)")
    else:
        print(f"❌ Python {version} (Requires Python 3.8+)")
    
    return major >= 3 and minor >= 8

def check_packages(packages: Dict[str, str], title: str) -> Dict[str, bool]:
    """Check a dictionary of packages."""
    print_section(title)
    results = {}
    
    # Special import name mappings
    import_mappings = {
        'langchain_openai': 'langchain_openai',
        'langchain_community': 'langchain_community',
        'streamlit_folium': 'streamlit_folium',
        'python_dateutil': 'dateutil',
        'dotenv': 'dotenv',
    }
    
    for package, description in packages.items():
        import_name = import_mappings.get(package, package)
        is_installed, version_info = check_package(package, import_name)
        
        if is_installed:
            print(f"✅ {package:<20} {version_info:<15} - {description}")
            results[package] = True
        else:
            pip_version = get_pip_version(package)
            if pip_version != "Not found":
                print(f"⚠️  {package:<20} {pip_version:<15} - {description} (Import issue)")
                results[package] = False
            else:
                print(f"❌ {package:<20} {'Not installed':<15} - {description}")
                results[package] = False
    
    return results

def generate_install_commands(missing_packages: List[str]):
    """Generate pip install commands for missing packages."""
    if not missing_packages:
        return
    
    print_section("Installation Commands")
    print("Run these commands to install missing packages:")
    print()
    
    # Group packages for efficient installation
    core_packages = []
    optional_packages = []
    
    for package in missing_packages:
        if package in REQUIRED_PACKAGES:
            core_packages.append(package)
        else:
            optional_packages.append(package)
    
    if core_packages:
        print("# Core packages (required)")
        if len(core_packages) <= 5:
            print(f"pip install {' '.join(core_packages)}")
        else:
            # Split into smaller groups
            for i in range(0, len(core_packages), 5):
                group = core_packages[i:i+5]
                print(f"pip install {' '.join(group)}")
        print()
    
    if optional_packages:
        print("# Optional packages")
        print(f"pip install {' '.join(optional_packages)}")
        print()
    
    print("# Or install everything from requirements.txt:")
    print("pip install -r requirements.txt")

def check_streamlit_config():
    """Check Streamlit configuration."""
    print_section("Streamlit Configuration")
    
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
        
        # Check if we can access streamlit config
        try:
            # This will work in a Streamlit app context
            config_exists = hasattr(st, 'secrets')
            print(f"✅ Streamlit secrets access: {'Available' if config_exists else 'Not in app context'}")
        except Exception:
            print("ℹ️  Streamlit secrets: Not in app context (normal when running outside Streamlit)")
            
    except ImportError:
        print("❌ Streamlit not installed")

def main():
    """Main function to run all checks."""
    print_header()
    
    # Check Python version
    python_ok = check_python_version()
    
    if not python_ok:
        print("\n❌ Python version incompatible. Please upgrade to Python 3.8 or higher.")
        sys.exit(1)
    
    # Check required packages
    required_results = check_packages(REQUIRED_PACKAGES, "Required Packages")
    
    # Check optional packages
    optional_results = check_packages(OPTIONAL_PACKAGES, "Optional Packages")
    
    # Check Streamlit configuration
    check_streamlit_config()
    
    # Summary
    print_section("Summary")
    required_missing = [pkg for pkg, installed in required_results.items() if not installed]
    optional_missing = [pkg for pkg, installed in optional_results.items() if not installed]
    
    total_required = len(REQUIRED_PACKAGES)
    installed_required = len([x for x in required_results.values() if x])
    
    print(f"Required packages: {installed_required}/{total_required} installed")
    
    if required_missing:
        print(f"❌ Missing required packages: {len(required_missing)}")
        print(f"   {', '.join(required_missing)}")
    else:
        print("✅ All required packages are installed!")
    
    if optional_missing:
        print(f"ℹ️  Missing optional packages: {len(optional_missing)}")
        print(f"   {', '.join(optional_missing)}")
    
    # Generate install commands
    all_missing = required_missing + optional_missing
    if all_missing:
        generate_install_commands(all_missing)
    
    print("\n" + "=" * 70)
    
    if required_missing:
        print("❌ Some required packages are missing. Please install them before running LogiBot.")
        return False
    else:
        print("✅ All required dependencies are satisfied! LogiBot should work properly.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)