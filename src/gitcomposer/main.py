import click
import subprocess
import os
import shutil

@click.command()
@click.argument('path', default='.', type=click.Path(exists=True, file_okay=False, resolve_path=True))
def cli(path):
    """
    Generates and executes a commit for a Git repository using the Gemini CLI.

    PATH: The path to start searching for a git repository from. Defaults to the current directory.
    """
    if not shutil.which("gemini"):
        click.echo("Error: The 'gemini' CLI is not installed or not in your PATH.", err=True)
        click.echo("Please install it using: npm install -g @google/gemini-cli", err=True)
        return

    try:
        root_process = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        repo_root = root_process.stdout.strip()
        click.echo(f"Found repository root at: {repo_root}")

        diff_process = subprocess.run(
            ['git', 'diff', '--staged'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        git_diff = diff_process.stdout

        if not git_diff:
            click.echo("No staged changes to commit. Use 'git add' to stage your changes.")
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
            ['gemini', 'chat', prompt],
            capture_output=True,
            text=True,
            check=True
        )
        commit_message = gemini_process.stdout.strip()

        click.echo("\n✨ Suggested Commit Message ✨")
        click.echo("---------------------------------")
        click.echo(commit_message)
        click.echo("---------------------------------")

        if not click.confirm("\nDo you want to commit with this message?", default=True):
            click.echo("Commit aborted by user.")
            return

        click.echo("Committing changes...")
        commit_process = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        click.echo("\n✅ Commit successful!")
        click.echo(commit_process.stdout)

    except subprocess.CalledProcessError as e:
        if 'gemini' in e.cmd:
            click.echo("\n❌ Error: The Gemini CLI failed to generate a commit message.", err=True)
            click.echo("Please check the following:", err=True)
            click.echo("  1. You have a stable internet connection.", err=True)
            click.echo("  2. The Gemini CLI is correctly configured with an API key (`gemini auth`).", err=True)
            click.echo("\nTo debug further, you can try running the 'gemini' command directly.", err=True)
        else:
            error_message = e.stderr
            if "not a git repository" in error_message:
                click.echo(f"Error: The path '{path}' is not inside a Git repository.", err=True)
            else:
                click.echo(f"\nAn error occurred while running a Git command:", err=True)
                click.echo(f"Command: {' '.join(e.cmd)}", err=True)
                click.echo(f"Error Message: {error_message}", err=True)

    except FileNotFoundError:
        click.echo("Error: 'git' command not found. Make sure Git is installed and in your PATH.", err=True)

if __name__ == '__main__':
    cli()