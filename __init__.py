# __init__.py

import os
import sys
import subprocess
import logging

# --- Configuration ---
NODE_NAME = "ComfyUI Google Drive Uploader"
PACKAGE_NAME = "comfyui_gdrive_uploader" # Should match the directory name

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Dependency Installation on Startup (Optional but recommended for git clone scenario) ---
def is_package_installed(package_name):
    """Checks if a package is installed in the current environment."""
    try:
        import importlib.util
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except (ImportError, AttributeError):
        return False

def install_requirements(requirements_file_path):
    """Installs packages listed in a requirements.txt file."""
    try:
        logger.info(f"Installing dependencies from {requirements_file_path}...")
        # Use the same Python executable that's running ComfyUI
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file_path])
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        # Depending on your needs, you might want to raise an exception here
        # to prevent the node from loading if dependencies are critical.
        # raise RuntimeError(f"Could not install required packages: {e}") from e

# --- Check and Install Dependencies on Import ---
# This block runs when the package is imported (i.e., when ComfyUI loads nodes)
requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
dependencies_installed = all(
    is_package_installed(pkg.split('==')[0].split('>=')[0].split('>')[0]) # Basic check for package name
    for pkg in open(requirements_path).read().strip().split('\n')
    if pkg and not pkg.startswith('#')
)

if not dependencies_installed:
    logger.warning(f"Dependencies for {NODE_NAME} might be missing. Attempting to install...")
    if os.path.exists(requirements_path):
        install_requirements(requirements_path)
    else:
        logger.error(f"Requirements file not found at {requirements_path}. Cannot auto-install dependencies.")
else:
    logger.info(f"Dependencies for {NODE_NAME} appear to be satisfied.")

# --- Node Registration ---
# Import the node class after ensuring dependencies *might* be available
# Note: If installation just started in the background, importing might still fail
# if it's the very first run. ComfyUI might need a restart after initial install.
from .gdrive_uploader_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS


# Import the OneDrive node class
from .onedrive_uploader_node import NODE_CLASS_MAPPINGS as ONEDRIVE_NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as ONEDRIVE_NODE_DISPLAY_NAME_MAPPINGS

# Merge the mappings
NODE_CLASS_MAPPINGS.update(ONEDRIVE_NODE_CLASS_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(ONEDRIVE_NODE_DISPLAY_NAME_MAPPINGS)


# --- Export Symbols ---
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
