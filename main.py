"""
This module sets up the environment and runs the main application.
"""

import argparse
import os

from dotenv import load_dotenv

from app.log.logging_config import configure_logger


def load_env():
    """
    Load environment variables from a dotenv file.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--env', type=str, default='local', help='Environment (e.g., dev, local, prod)'
    )
    args, _ = parser.parse_known_args()
    dotenv_path = os.path.join('env', f'{args.env}.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded dotenv file: {dotenv_path}")
    else:
        print(f"Dotenv file not found: {dotenv_path}")


if __name__ == '__main__':
    load_env()
    configure_logger()
    # Import main after environment is loaded so that
    # all modules (like logging_config) pick up the env vars.
    from app.run import run

    run()
