
import streamlit as st
import subprocess
import os

def run_conversion(source_dir, target_dir, soffice_path):
    """
    Runs the convert_corpus.py script with the given arguments.
    """
    command = [
        "python",
        "convert_corpus.py",
        source_dir,
        target_dir,
        "--soffice-path",
        soffice_path,
    ]

    st.info(f"Pokrećem konverziju sa komandom: {' '.join(command)}")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        stdout_output = []
        stderr_output = []

        # Real-time output display
        st.subheader("Izlaz iz skripte:")
        output_area = st.empty()

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                stdout_output.append(output)
                output_area.code("".join(stdout_output))
        
        # Capture remaining stderr
        stderr_output = process.stderr.readlines()

        return_code = process.poll()

        if return_code == 0:
            st.success("Konverzija uspešno završena!")
        else:
            st.error(f"Konverzija neuspešna! Povratni kod: {return_code}")
            if stdout_output:
                st.error("STDOUT:")
                st.code("".join(stdout_output))
            if stderr_output:
                st.error("STDERR:")
                st.code("".join(stderr_output))

    except FileNotFoundError:
        st.error(
            "Greška: Python ili convert_corpus.py skripta nisu pronađeni. Proverite putanje."
        )
    except Exception as e:
        st.error(f"Došlo je do neočekivane greške: {e}")

st.set_page_config(page_title="DOC u DOCX Konvertor", layout="centered")
st.title("DOC u DOCX Konvertor")
st.markdown("Koristite ovu aplikaciju za konverziju .doc fajlova u .docx format koristeći `soffice`.")

# Input fields
source_directory = st.text_input(
    "Izvorni direktorijum (.doc fajlovi):",
    placeholder="Unesite putanju do direktorijuma sa .doc fajlovima",
    value=os.getcwd() # Default to current working directory
)

target_directory = st.text_input(
    "Odredišni direktorijum (.docx fajlovi):",
    placeholder="Unesite putanju gde će se sačuvati .docx fajlovi",
    value=os.path.join(os.getcwd(), "converted_docs") # Default to a subfolder
)

soffice_path = st.text_input(
    "Putanja do soffice izvršne datoteke (npr. C:\\Program Files\\LibreOffice\\program\\soffice.exe):",
    placeholder="Unesite putanju do soffice.exe",
    value="soffice" # Default to "soffice" assuming it's in PATH
)

# Conversion button
if st.button("Pokreni konverziju"):
    if not source_directory or not target_directory:
        st.warning("Molimo unesite i izvorni i odredišni direktorijum.")
    else:
        # Ensure target directory exists before running conversion
        os.makedirs(target_directory, exist_ok=True)
        run_conversion(source_directory, target_directory, soffice_path)

st.markdown("---")
st.markdown("### Uputstvo:")
st.markdown("1. **Izvorni direktorijum:** Unesite putanju do foldera koji sadrži vaše `.doc` fajlove.")
st.markdown("2. **Odredišni direktorijum:** Unesite putanju do foldera gde želite da sačuvate konvertovane `.docx` fajlove. Ako folder ne postoji, biće kreiran.")
st.markdown("3. **Putanja do soffice:** Unesite punu putanju do `soffice.exe` (npr. `C:\\Program Files\\LibreOffice\\program\\soffice.exe`). Ako je `soffice` u vašem PATH-u, možete ostaviti `soffice`.")
st.markdown("4. Kliknite na **Pokreni konverziju**.")

st.info("Napomena: Logovi konverzije će biti sačuvani u `conversion_log.txt` fajlu u istom direktorijumu gde se nalazi `convert_corpus.py`.")
