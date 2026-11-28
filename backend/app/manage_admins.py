"""Manage admin accounts from the command line. There's deliberately no way to
create an account from the website, so only someone with access to the server
can make one.

Run from the backend folder:

    python -m app.manage_admins add <username>      create an account, or change its password
    python -m app.manage_admins remove <username>
    python -m app.manage_admins list

Passwords are typed at a prompt, never on the command line (where they'd end
up in your shell history). In a normal terminal the typing is hidden. Git Bash
doesn't give Python a real console, so there the typing shows on screen
instead; clear the screen afterwards if anyone is looking.
"""

import argparse
import getpass
import sys

from app import admin_accounts


def ask_password(prompt: str) -> str:
    # getpass hides what you type, but needs a real console. Git Bash's
    # terminal isn't one, and there getpass can hang without showing a prompt,
    # so fall back to a normal (visible) prompt.
    if (sys.stdin.isatty()):
        return getpass.getpass(prompt)
    return input(prompt)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.manage_admins",
                                     description="Manage admin accounts.")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="create an admin account, or change its password")
    add.add_argument("username")
    remove = commands.add_parser("remove", help="delete an admin account")
    remove.add_argument("username")
    commands.add_parser("list", help="show all admin usernames")
    args = parser.parse_args(argv)

    if (args.command == "add"):
        if (not sys.stdin.isatty()):
            print("Note: this terminal can't hide typing, so the password will show as you type.",
                  flush=True)
        password = ask_password("Password: ")
        if (password != ask_password("Repeat password: ")):
            print("The passwords don't match. Nothing was saved.")
            return 1
        try:
            name = admin_accounts.set_password(args.username, password)
        except ValueError as error:
            print(error)
            return 1
        print(f"Saved admin account '{name}'.")
        return 0

    if (args.command == "remove"):
        if (admin_accounts.remove_account(args.username)):
            print(f"Removed admin account '{admin_accounts.normalize_username(args.username)}'.")
            return 0
        print("There's no admin account with that username.")
        return 1

    names = sorted(admin_accounts.load_accounts())
    print("\n".join(names) if names else "No admin accounts yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
