"""Test environment setup script for Legal Document Intelligence Platform."""

import logging
import os
import subprocess
import sys
from pathlib import Path


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_and_install_dependencies():
    """Check and install required dependencies."""
    try:
        import nltk
        import rouge_chinese
        import spacy

        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('wordnet')

        # Download Chinese language model for spaCy
        if not spacy.util.is_package("zh_core_web_sm"):
            subprocess.run([sys.executable, "-m", "spacy", "download", "zh_core_web_sm"], check=True)

        logging.info("Successfully installed and configured all dependencies")
    except ImportError as e:
        logging.error(f"Missing dependency: {e}")
        logging.info("Installing missing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)

        # Retry downloading after installation
        import nltk
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('wordnet')

def setup_python_path():
    """Setup PYTHONPATH to include the project root."""
    project_root = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, str(project_root))
    os.environ["PYTHONPATH"] = str(project_root)
    logging.info(f"PYTHONPATH set to: {project_root}")

def main():
    """Main setup function."""
    setup_logging()
    logging.info("Starting test environment setup...")

    try:
        setup_python_path()
        check_and_install_dependencies()
        logging.info("Test environment setup completed successfully")
    except Exception as e:
        logging.error(f"Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
