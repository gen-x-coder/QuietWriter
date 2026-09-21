import os
import re
import zipfile
import subprocess
import glob
import shutil
from datetime import datetime

# --- CONFIGURATIE ---
# De map waar je zip-bestanden én dit script staan
ZIPS_FOLDER = r"C:\Users\lucas\Downloads\QuietWriter\Builds\build"

# Je hoofdproject map van Git
REPO_FOLDER = r"C:\Users\lucas\Downloads\QuietWriter"  

# Je GitHub repository URL
REMOTE_URL = "https://github.com/gen-x-coder/QuietWriter.git"

def run_git(cmd, cwd):
    """Voert een git commando uit en retourneert het resultaat."""
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

def check_git_environment():
    print("Bezig met uitvoeren van omgevingschecks...")
    
    # 1. Check of git beschikbaar is
    success, _, _ = run_git(["git", "--version"], REPO_FOLDER)
    if not success:
        print("FOUT: Git is niet geïnstalleerd of niet gevonden in het systeempad.")
        return False

    # 2. Check of de map een git repo is, zo niet initialiseren
    if not os.path.exists(os.path.join(REPO_FOLDER, ".git")):
        print(f"Initialiseer nieuwe Git repository in {REPO_FOLDER}...")
        success, _, err = run_git(["git", "init"], REPO_FOLDER)
        if not success:
            print(f"FOUT bij git init: {err}")
            return False

    # 3. Check of remote gekoppeld is
    success, out, _ = run_git(["git", "remote", "get-url", "origin"], REPO_FOLDER)
    if not success or not out:
        print(f"Koppel remote origin naar {REMOTE_URL}...")
        run_git(["git", "remote", "add", "origin", REMOTE_URL], REPO_FOLDER)
    else:
        print(f"Remote origin is correct ingesteld op: {out}")

    # 4. Check of de gebruiker verbinding kan maken met GitHub
    print("Controleren van GitHub verbinding en authenticatie...")
    success, out, err = run_git(["git", "ls-remote", REMOTE_URL], REPO_FOLDER)
    if not success:
        print("\n[WAARSCHUWING / FOUT] Kan geen verbinding maken met de GitHub repository.")
        print(f"Technische foutmelding: {err}")
        return False
    
    print("Verbinding met GitHub succesvol geverifieerd!")
    return True

def extract_version_from_filename(filename):
    """Haalt het versienummer uit de bestandsnaam, bijv 'QuietWriter-1.2.2.zip' -> '1.2.2'"""
    match = re.search(r'(\d+\.\d+\.\d+|\d+\.\d+)', filename)
    return match.group(1) if match else None

def main():
    if not os.path.exists(ZIPS_FOLDER):
        print(f"FOUT: De map met zips bestaat niet: {ZIPS_FOLDER}")
        return

    os.makedirs(REPO_FOLDER, exist_ok=True)

    # Voer de veiligheidschecks uit
    if not check_git_environment():
        print("\nScript afgebroken vanwege falende checks.")
        return

    # Zoek alle zips en sorteer ze op basis van de bestandsdatum (oudste eerst)
    zip_files = glob.glob(os.path.join(ZIPS_FOLDER, "*.zip"))
    if not zip_files:
        print(f"Geen zip-bestanden gevonden in {ZIPS_FOLDER}!")
        return

    zip_files.sort(key=os.path.getmtime)

    print(f"\nTotaal {len(zip_files)} builds gevonden. Start verwerking in chronologische volgorde...\n")

    # Bepaal absolute paden die NOOIT gewist mogen worden
    abs_repo = os.path.abspath(REPO_FOLDER)
    abs_builds = os.path.abspath(os.path.join(abs_repo, "Builds"))

    for index, zip_path in enumerate(zip_files):
        filename = os.path.basename(zip_path)
        version = extract_version_from_filename(filename)
        
        if not version:
            print(f"[{index+1}/{len(zip_files)}] Kan geen versie ontdekken in {filename}, overslaan.")
            continue
            
        tag_name = f"v{version}"
        file_mtime = os.path.getmtime(zip_path)
        commit_date = datetime.fromtimestamp(file_mtime).isoformat()
        
        print(f"[{index+1}/{len(zip_files)}] Verwerken: {filename} -> Versie {version} (Datum: {commit_date[:10]})")

        # 1. Maak repo leeg, maar sla .git en de gehele 'Builds' map strikt over
        for item in os.listdir(abs_repo):
            item_path = os.path.abspath(os.path.join(abs_repo, item))
            
            # Altijd overslaan: .git en de Builds map (en alles daarbinnen)
            if item.lower() == ".git" or item_path == abs_builds or abs_builds.startswith(item_path):
                continue
                
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        # 2. Pak de zip uit in de repo map
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(REPO_FOLDER)
        except Exception as e:
            print(f"  -> FOUT bij uitpakken: {e}")
            continue

        # 3. Git add & commit met historische datum
        run_git(["git", "add", "-A"], REPO_FOLDER)
        
        status_res, stdout, _ = run_git(["git", "status", "--porcelain"], REPO_FOLDER)
        if not stdout.strip():
            print(f"  -> Geen wijzigingen voor {version}, overslaan.")
            continue

        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = commit_date
        env["GIT_COMMITTER_DATE"] = commit_date
        
        commit_msg = f"Release {version}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_FOLDER, env=env, capture_output=True)

        # 4. Maak de tag aan
        run_git(["git", "tag", "-f", tag_name], REPO_FOLDER)

    print("\n" + "="*50)
    print("Klaar met het opbouwen van de lokale historie!")
    print("Je kunt nu pushen met: git push origin main --tags --force")

if __name__ == "__main__":
    main()