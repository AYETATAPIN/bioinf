import subprocess
from pathlib import Path

from mage_ai.data_preparation.decorators import custom


@custom
def transform_custom(data, *args, **kwargs):
    assignment_dir = Path(data['assignment_dir'])
    script = Path(data['script'])
    log_path = assignment_dir / 'logs' / 'mage_mapping_qc.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        ['bash', str(script)],
        cwd=str(assignment_dir),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log_path.write_text(completed.stdout, encoding='utf-8')

    return {
        **data,
        'returncode': completed.returncode,
        'mage_log': str(log_path),
        'flagstat': str(assignment_dir / 'results' / 'flagstat.txt'),
        'qc_result': str(assignment_dir / 'results' / 'mapping_qc_result.txt'),
    }
