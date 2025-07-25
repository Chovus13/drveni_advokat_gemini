 
import os
import subprocess
import logging
import argparse

# Configure logging
logging.basicConfig(
    filename='conversion_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def convert_doc_to_docx(
    source_dir: str,
    target_dir: str,
    soffice_path: str = "soffice"
):
    """
    Recursively scans a directory for .doc files and converts them to .docx using soffice.
    Logs the conversion status and provides resumability.

    Args:
        source_dir (str): The root directory to scan for .doc files.
        target_dir (str): The root directory where converted .docx files will be saved.
        soffice_path (str): The path to the soffice executable. Defaults to "soffice".
    """
    logging.info(f"Starting conversion from '{source_dir}' to '{target_dir}'")

    for root, _, files in os.walk(source_dir):
        relative_path = os.path.relpath(root, source_dir)
        current_target_dir = os.path.join(target_dir, relative_path)

        os.makedirs(current_target_dir, exist_ok=True)

        for file in files:
            if file.lower().endswith(".doc"):
                source_file_path = os.path.join(root, file)
                target_file_name = os.path.splitext(file)[0] + ".docx"
                target_file_path = os.path.join(current_target_dir, target_file_name)

                if os.path.exists(target_file_path):
                    logging.info(
                        f"Skipping: '{source_file_path}' - Target '{target_file_path}' already exists."
                    )
                    continue

                logging.info(f"Attempting to convert: '{source_file_path}'")
                command = [
                    soffice_path,
                    "--headless",
                    "--convert-to",
                    "docx",
                    "--outdir",
                    current_target_dir,
                    source_file_path,
                ]

                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        check=False,
                        encoding="utf-8",
                        errors="replace",
                    )

                    if result.returncode == 0:
                        logging.info(
                            f"SUCCESS: '{source_file_path}' converted to '{target_file_path}'"
                        )
                        if result.stdout:
                            logging.debug(f"STDOUT: {result.stdout.strip()}")
                    else:
                        logging.error(
                            f"FAILED: '{source_file_path}' - Return Code: {result.returncode}"
                        )
                        if result.stdout:
                            logging.error(f"STDOUT: {result.stdout.strip()}")
                        if result.stderr:
                            logging.error(f"STDERR: {result.stderr.strip()}")

                except FileNotFoundError:
                    logging.error(
                        f"ERROR: soffice not found. Please ensure LibreOffice/OpenOffice is installed and 'soffice' is in your PATH, or provide the full path to 'soffice'."
                    )
                    return  # Exit if soffice is not found
                except Exception as e:
                    logging.error(
                        f"AN UNEXPECTED ERROR OCCURRED during conversion of '{source_file_path}': {e}"
                    )

    logging.info("Conversion process completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert .doc files to .docx using soffice."
    )
    parser.add_argument(
        "source_directory", type=str, help="The root directory to scan for .doc files."
    )
    parser.add_argument(
        "target_directory",
        type=str,
        help="The root directory where converted .docx files will be saved.",
    )
    parser.add_argument(
        "--soffice-path",
        type=str,
        default="soffice",
        help="Optional: Path to the soffice executable (e.g., /usr/bin/soffice). Defaults to 'soffice' (assumes it's in PATH).",
    )

    args = parser.parse_args()

    convert_doc_to_docx(args.source_directory, args.target_directory, args.soffice_path)
