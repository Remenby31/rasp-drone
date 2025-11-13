#!/usr/bin/env python3
"""
Script pour envoyer des commandes CLI à iNAV via MSP
Permet d'exécuter n'importe quelle commande CLI depuis Python

Usage:
    python3 send_cli_command.py "get receiver_type"
    python3 send_cli_command.py "status"
    python3 send_cli_command.py "set beeper_off_flags = DISARMING" "save"
"""

import serial
import time
import sys

class INavCLI:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def connect(self):
        """Ouvre la connexion série"""
        self.ser = serial.Serial(self.port, self.baudrate, timeout=2.0)
        time.sleep(0.5)
        print(f"✓ Connecté à {self.port}")

    def enter_cli(self):
        """Entre en mode CLI"""
        # Envoyer le caractère '#' pour entrer en CLI
        self.ser.write(b'#')
        time.sleep(0.5)

        # Lire la réponse (bannière CLI)
        response = b''
        start_time = time.time()
        while time.time() - start_time < 2.0:
            if self.ser.in_waiting:
                response += self.ser.read(self.ser.in_waiting)
                time.sleep(0.1)
            else:
                break

        if b'CLI' in response or b'#' in response:
            print("✓ Mode CLI activé")
            return True
        else:
            print("⚠️  Réponse CLI:", response.decode('utf-8', errors='ignore'))
            return True  # On continue quand même

    def send_command(self, command):
        """Envoie une commande CLI et retourne la réponse"""
        # Envoyer la commande
        cmd = command.strip() + '\r\n'
        self.ser.write(cmd.encode('utf-8'))

        # Attendre et lire la réponse
        time.sleep(0.3)
        response = b''
        start_time = time.time()

        while time.time() - start_time < 2.0:
            if self.ser.in_waiting:
                chunk = self.ser.read(self.ser.in_waiting)
                response += chunk
                time.sleep(0.1)
            else:
                if len(response) > 0:
                    break

        # Décoder et nettoyer la réponse
        output = response.decode('utf-8', errors='ignore')

        # Retirer l'écho de la commande et le prompt
        lines = output.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            # Ignorer les lignes vides, l'écho de commande et le prompt
            if line and line != command and not line.startswith('#'):
                clean_lines.append(line)

        return '\n'.join(clean_lines)

    def exit_cli(self):
        """Sort du mode CLI"""
        self.ser.write(b'exit\r\n')
        time.sleep(0.5)
        print("✓ Mode CLI quitté")

    def close(self):
        """Ferme la connexion série"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("✓ Connexion fermée")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 send_cli_command.py <commande1> [commande2] ...")
        print("\nExemples:")
        print('  python3 send_cli_command.py "get receiver_type"')
        print('  python3 send_cli_command.py "status"')
        print('  python3 send_cli_command.py "set beeper_off_flags = DISARMING" "save"')
        print('  python3 send_cli_command.py "get beeper_off_flags"')
        sys.exit(1)

    commands = sys.argv[1:]

    print("=" * 60)
    print("🖥️  iNAV CLI via MSP")
    print("=" * 60)

    cli = INavCLI()

    try:
        print("\n[1/4] Connexion au FC...")
        cli.connect()

        print("\n[2/4] Entrée en mode CLI...")
        cli.enter_cli()

        print("\n[3/4] Exécution des commandes...")
        for i, cmd in enumerate(commands, 1):
            print(f"\n📤 Commande {i}/{len(commands)}: {cmd}")
            response = cli.send_command(cmd)
            if response:
                print("📥 Réponse:")
                print(response)
            else:
                print("📥 (Pas de réponse)")

        print("\n[4/4] Sortie du CLI...")
        cli.exit_cli()

        print("\n" + "=" * 60)
        print("✅ Terminé")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

    finally:
        cli.close()

if __name__ == "__main__":
    main()
