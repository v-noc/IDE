from typing import Optional
import uuid
import os
import subprocess
import shlex
from pydantic import BaseModel


class CodeResponse(BaseModel):
    response: str
    has_error: bool


class CodeRunner:

    def run_code(
        self,
        project_root_path: str,
        python_executable: Optional[str],
        code: str,
        *,
        examples_path: Optional[str] = None,
        command_prefix: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> CodeResponse:
        """Run code either using a direct python executable or a custom
        command prefix.

        When command_prefix is provided, the code is written into
        project_root_path/examples_path/<filename> and executed via
        `<command_prefix> <absolute_file_path>`.

        Otherwise, it falls back to using the python_executable directly
        on a temp file in project_root_path.
        """

        temp_filepath: Optional[str] = None
        try:
            if command_prefix:
                # Ensure destination directory
                target_dir = (
                    os.path.join(project_root_path, examples_path)
                    if examples_path
                    else project_root_path
                )
                os.makedirs(target_dir, exist_ok=True)
                temp_filename = filename or f"__ide_example_{uuid.uuid4()}.py"
                temp_filepath = os.path.join(target_dir, temp_filename)

                with open(temp_filepath, "w") as f:
                    f.write(code)

                # Build command safely
                prefix_parts = shlex.split(command_prefix)
                command = prefix_parts + [temp_filepath]
            else:
                # Default to python execution at project root
                temp_filename = f"__ide_runner_{uuid.uuid4()}.py"
                temp_filepath = os.path.join(project_root_path, temp_filename)
                with open(temp_filepath, "w") as f:
                    f.write(code)

                python_cmd = python_executable or "python"
                command = [python_cmd, temp_filepath]

            proc = subprocess.run(
                command,
                cwd=project_root_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if proc.returncode == 0:
                return CodeResponse(response=proc.stdout, has_error=False)
            return CodeResponse(response=proc.stderr, has_error=True)

        finally:
            # Cleanup temp file if created
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except Exception:
                    # Best-effort cleanup; ignore failures
                    pass
