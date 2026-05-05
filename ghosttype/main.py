"""GhostType main entry point."""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghosttype_desktop.app import GhostTypeDesktopApp, create_app


def main():
    """Main entry point for GhostType."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app = create_app()

    print(f"GhostType started")
    print(f"Audio available: {app._recorder is not None}")
    print(f"Input available: {app._input_provider is not None}")
    print(f"Router available: {app._router is not None}")

    return app


if __name__ == "__main__":
    main()
