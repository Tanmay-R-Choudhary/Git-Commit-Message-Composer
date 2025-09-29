import click
import subprocess
import os
import shutil


@click.command()
@click.argument(
    "path",
    default=".",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
)
def cli(path):
    """
    Generates and executes a commit for a Git repository using the Gemini CLI.

    PATH: The path to the local git repository. Defaults to the current directory.
    """
    if not shutil.which("gemini"):
        click.echo(
            "Error: The 'gemini' CLI is not installed or not in your PATH.", err=True
        )
        click.echo(
            "Please install it using: npm install -g @google/gemini-cli", err=True
        )
        return

    click.echo(f"Analyzing repository at: {path}")

    try:
        if not os.path.isdir(os.path.join(path, ".git")):
            click.echo("Error: The provided path is not a Git repository.", err=True)
            return

        diff_process = subprocess.run(
            ["git", "diff", "--staged"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        git_diff = diff_process.stdout

        if not git_diff:
            click.echo(
                "No staged changes to commit. Use 'git add' to stage your changes."
            )
            return

        prompt = (
            "You are an expert programmer. Your task is to write a concise and conventional "
            "commit message based on the following git diff. The message should be in the imperative mood, "
            "for example, 'Add feature' not 'Added feature'. Do not include any preamble or backticks.\n\n"
            "--- GIT DIFF ---\n"
            f"{git_diff}"
            "\n--- END GIT DIFF ---\n\n"
            "Commit message:"
        )

        click.echo("Sending staged changes to Gemini to generate a commit message...")

        gemini_process = subprocess.run(
            ["gemini", "chat", prompt], capture_output=True, text=True, check=True
        )
        commit_message = gemini_process.stdout.strip()

        click.echo("\n✨ Suggested Commit Message ✨")
        click.echo("---------------------------------")
        click.echo(commit_message)
        click.echo("---------------------------------")

        # --- NEW CODE STARTS HERE ---

        # 1. Ask the user for confirmation before committing
        if not click.confirm(
            "\nDo you want to commit with this message?", default=True
        ):
            click.echo("Commit aborted by user.")
            return

        # 2. If confirmed, run the git commit command
        click.echo("Committing changes...")
        commit_process = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        # 3. Print the output from the git commit command
        click.echo("\n✅ Commit successful!")
        click.echo(commit_process.stdout)

    except subprocess.CalledProcessError as e:
        click.echo(f"\nAn error occurred while running an external command:", err=True)
        click.echo(f"Command: {' '.join(e.cmd)}", err=True)
        click.echo(f"Error Message: {e.stderr}", err=True)
    except FileNotFoundError:
        click.echo(
            "Error: 'git' command not found. Make sure Git is installed and in your PATH.",
            err=True,
        )


if __name__ == "__main__":
    cli()
