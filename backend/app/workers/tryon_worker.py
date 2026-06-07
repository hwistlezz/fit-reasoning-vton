import traceback
from pathlib import Path

from backend.app.core.job_store import (
    get_existing_job_dir,
    mark_job_running,
    write_failed_result,
    write_success_result,
)
from backend.app.services.stableviton_input_adapter import (
    StableVitonInputAdapterError,
    preflight_required_artifacts,
    prepare_stableviton_input,
)
from backend.app.services.stableviton_service import StableVitonServiceError, run_stableviton_inference


def _write_error_logs_if_missing(job_dir: Path, code: str, message: str) -> None:
    stdout_log = job_dir / "stableviton_stdout.log"
    stderr_log = job_dir / "stableviton_stderr.log"
    if not stdout_log.is_file():
        stdout_log.write_text("", encoding="utf-8")
    if not stderr_log.is_file():
        stderr_log.write_text(f"{code}: {message}\n", encoding="utf-8")


def run_tryon_job(job_id: str) -> None:
    job_dir = get_existing_job_dir(job_id)

    try:
        mark_job_running(job_id)
        stableviton_input = prepare_stableviton_input(job_id)
        preflight_required_artifacts(stableviton_input)
        run_result = run_stableviton_inference(job_id, job_dir, data_root=stableviton_input.data_root)
        write_success_result(job_id, run_result.result_path.name)
    except StableVitonInputAdapterError as exc:
        _write_error_logs_if_missing(job_dir, exc.code, exc.message)
        write_failed_result(job_id, exc.code, exc.message)
    except StableVitonServiceError as exc:
        _write_error_logs_if_missing(job_dir, exc.code, exc.message)
        write_failed_result(job_id, exc.code, exc.message)
    except Exception:
        code = "STABLEVITON_INFERENCE_FAILED"
        message = "Unexpected StableVITON wrapper error. Check logs for details."
        _write_error_logs_if_missing(job_dir, code, traceback.format_exc())
        write_failed_result(job_id, code, message)
