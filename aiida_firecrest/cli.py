"""Simple CLI for FireCrest."""
import json
import tempfile
from pathlib import Path
from typing import Optional

import click
import firecrest as f7t
import yaml

from .transport import FirecrestTransport


class Connection:
    """Connection data FireCrest."""

    def __init__(self) -> None:
        """Initialize the connection."""
        self._path: Optional[Path] = None
        self._info: Optional[dict] = None

    def set_path(self, path: Path) -> None:
        """Set the path."""
        self._path = path

    @property
    def info(self) -> dict:
        """Get the info."""
        if self._info is not None:
            return self._info
        if self._path is None:
            raise ValueError("Path not set")
        info = json.loads(self._path.read_text())
        assert set(info).issuperset(
            {
                "url",
                "token_uri",
                "client_id",
                "client_secret",
                "machine",
            }
        )
        self._info = info
        return self._info

    @property
    def transport(self) -> FirecrestTransport:
        """Get the transport."""
        transport = FirecrestTransport(**self.info)
        if "scratch_path" in self.info:
            transport.chdir(self.info["scratch_path"], check_exists=False)
        return transport

    @property
    def client(self) -> f7t.Firecrest:
        """Get the client."""
        return self.transport._client


connection = click.make_pass_decorator(Connection, ensure=True)


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to the connection file (default: .firecrest-config.json).",
)
@connection
def main(connection, config):
    """FireCrest CLI."""
    if config is not None:
        connection.set_path(config)
    else:
        connection.set_path(Path.cwd() / ".firecrest-config.json")


@main.command("parameters")
@connection
def parameters(connection: Connection):
    """Get parameters that can be configured in environment files."""
    print(yaml.dump(connection.client.parameters()))


@main.command("services")
@connection
def services(connection: Connection):
    """List available services."""
    click.echo(yaml.dump(connection.client.all_services()))


@main.command("service")
@click.argument("service")
@connection
def service(connection: Connection, service: str):
    """Information about a service."""
    click.echo(yaml.dump(connection.client.service(service)))


@main.command("systems")
@connection
def systems(connection: Connection):
    """List available systems."""
    click.echo(yaml.dump(connection.client.all_systems()))


@main.command("system")
@click.argument("system")
@connection
def system(connection: Connection, system: str):
    """Information about a system."""
    click.echo(yaml.dump(connection.client.system(system)))


@main.command("cwd")
@connection
def cwd(connection: Connection):
    """Get the current working directory."""
    click.echo(connection.transport.getcwd())


@main.command("ls")
@click.argument("path", default=".")
@connection
def ls(connection: Connection, path: str):
    """List files in a path."""
    # todo want to allow for '/' to prepend folders here?
    click.echo(" ".join(connection.transport.listdir(path)))


@main.command("stat")
@click.argument("path")
@connection
def stat(connection: Connection, path: str):
    """Get information about a file."""
    click.echo(yaml.dump(connection.transport.stat(path)))


@main.command("chmod")
@click.argument("path")
@click.argument("mode")
@connection
def chmod(connection: Connection, path: str, mode: str):
    """Change the mode of a file."""
    connection.transport.chmod(path, mode)
    click.secho(f"Changed mode of {path} to {mode}", fg="green")


@main.command("putfile")
@click.argument("source_path")
@click.argument("target_path")
@connection
def putfile(connection: Connection, source_path: str, target_path: str):
    """Upload file to the remote."""
    connection.transport.putfile(source_path, target_path)
    click.secho(f"Uploaded {source_path} to {target_path}", fg="green")


@main.command("cat")
@click.argument("path")
@connection
def cat(connection: Connection, path: str):
    """Get the contents of a file."""
    with tempfile.NamedTemporaryFile() as f:
        connection.transport.getfile(path, f.name)
        click.echo(f.read())
