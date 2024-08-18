import subprocess

# Command to run PyInstaller
command = [
    "pyinstaller",
    "--onefile",
    "--windowed",
    "--noupx",
    "--icon=assets/icon.ico",
    "application/app.py"
]

try:
    # Run PyInstaller and capture output
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Print the output of the command (for debugging purposes)
    print(result.stdout)
    print("PyInstaller executed successfully.")
except subprocess.CalledProcessError as e:
    # Print the error output
    print("PyInstaller failed.")
    print(e.stderr)
