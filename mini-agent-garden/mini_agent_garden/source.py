"""Read immutable implementation trees from the local Git object database."""

from __future__ import annotations

from pathlib import Path
import subprocess

from .canonical import digest_bytes
from .canonical import digest_json
from .contracts import ImplementationSelection
from .errors import GardenError


class GitSourceReader:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _git(self, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            check=False,
        )

    def read_tree(
        self,
        selection: ImplementationSelection,
    ) -> tuple[dict[str, bytes], str]:
        prefix = selection.source_path.rstrip("/") + "/"
        listed = self._git(
            "ls-tree",
            "-r",
            "--name-only",
            selection.revision,
            "--",
            selection.source_path,
        )
        if listed.returncode != 0:
            raise GardenError(
                "cannot resolve pinned implementation tree: "
                + listed.stderr.decode(errors="replace").strip()
            )
        paths = [
            line
            for line in listed.stdout.decode().splitlines()
            if line
        ]
        if not paths:
            raise GardenError(
                f"pinned implementation tree is empty: {selection.source_path}"
            )
        files: dict[str, bytes] = {}
        for path in paths:
            if not path.startswith(prefix):
                raise GardenError(f"Git returned an out-of-scope path: {path}")
            relative = path[len(prefix) :]
            blob = self._git("show", f"{selection.revision}:{path}")
            if blob.returncode != 0:
                raise GardenError(f"cannot read pinned blob: {path}")
            files[relative] = blob.stdout
        tree_digest = digest_json(
            {
                path: digest_bytes(value)
                for path, value in sorted(files.items())
            }
        )
        return files, tree_digest
