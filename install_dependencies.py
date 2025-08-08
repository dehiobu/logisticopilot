#!/usr/bin/env python3
# ==============================================================================
# 🚀 LogiBot AI Copilot - Automated Dependency Installation
# ==============================================================================

import sys
import subprocess
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"🔄 {description}")
    print(f"   Running: {command}")
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Timeout")
        return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def check_pip():
    """Check if pip is available."""
    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                      capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def upgrade_pip():
    """Upgrade pip to latest version."""
    return run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Upgrading pip"
    )

def install_requirements():
    """Install from requirements.txt if it exists."""
    requirements_path = Path("requirements.txt")
    
    if requirements_path.exists():
        return run_command(
            f"{sys.executable} -m pip install -r requirements.txt",
            "Installing from requirements.txt"
        )
    else:
        print("⚠️  requirements.txt not found, installing core packages individually")
        return install_core_packages()

def install_core_packages():
    """Install core packages individually."""
    core_packages = [
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "xlsxwriter>=3.1.0",
        "langchain>=0.1.0",
        "langchain-openai>=0.0.8",
        "langchain-community>=0.0.20",
        "faiss-cpu>=1.7.4",
        "tiktoken>=0.5.0",
        "pydantic>=2.0.0",
        "plotly>=5.17.0",
        "folium>=0.14.0",
        "streamlit-folium>=0.13.0",
        "reportlab>=4.0.0",
        "jinja2>=3.1.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0"
    ]
    
    print(f"📦 Installing {len(core_packages)} core packages...")
    
    # Install in groups to avoid timeout
    group_size = 3
    for i in range(0, len(core_packages), group_size):
        group = core_packages[i:i+group_size]
        package_list = " ".join(group)
        
        success = run_command(
            f"{sys.executable} -m pip install {package_list}",
            f"Installing group {i//group_size + 1}: {', '.join([p.split('>=')[0] for p in group])}"
        )
        
        if not success:
            print(f"⚠️  Group installation failed, trying individual packages...")
            for package in group:
                run_command(
                    f"{sys.executable} -m pip install {package}",
                    f"Installing {package.split('>=')[0]}"
                )
    
    return True

def create_requirements_file():
    """Create a requirements.txt file if it doesn't exist."""
    requirements_content = """# LogiBot AI Copilot Dependencies
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
langchain>=0.1.0
langchain-openai>=0.0.8
langchain-community>=0.0.20
faiss-cpu>=1.7.4
tiktoken>=0.5.0
pydantic>=2.0.0
plotly>=5.17.0
folium>=0.14.0
streamlit-folium>=0.13.0
reportlab>=4.0.0
jinja2>=3.1.0
requests>=2.31.0
python-dotenv>=1.0.0
"""
    
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("📝 Creating requirements.txt...")
        requirements_path.write_text(requirements_content)
        print("✅ requirements.txt created")

def verify_installation():
    """Verify that key packages can be imported."""
    test_imports = [
        ('streamlit', 'Streamlit'),
        ('pandas', 'Pandas'),
        ('langchain', 'LangChain'),
        ('faiss', 'FAISS'),
        ('plotly', 'Plotly'),
    ]
    
    print("\n🔍 Verifying installation...")
    all_good = True
    
    for module_name, display_name in test_imports:
        try:
            __import__(module_name)
            print(f"✅ {display_name} - OK")
        except ImportError as e:
            print(f"❌ {display_name} - Failed: {e}")
            all_good = False
    
    return all_good

def main():
    """Main installation process."""
    print("=" * 60)
    print("🚀 LogiBot AI Copilot - Dependency Installation")
    print("=" * 60)
    
    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected")
        print("   LogiBot requires Python 3.8 or higher")
        sys.exit(1)
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    
    # Check pip
    if not check_pip():
        print("❌ pip not found. Please install pip first.")
        sys.exit(1)
    
    # Upgrade pip
    print("\n📈 Upgrading pip...")
    upgrade_pip()
    
    # Create requirements file if needed
    create_requirements_file()
    
    # Install packages
    print("\n📦 Installing packages...")
    install_requirements()
    
    # Verify installation
    if verify_installation():
        print("\n🎉 Installation completed successfully!")
        print("\n🚀 You can now run LogiBot with:")
        print("   streamlit run app.py")
    else:
        print("\n⚠️  Installation completed with some issues.")
        print("   You may need to install missing packages manually.")
        print("\n📋 To check what's missing, run:")
        print("   python check_dependencies.py")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()