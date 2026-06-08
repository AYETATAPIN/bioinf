from pathlib import Path

from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data(data, *args, **kwargs):
    assignment_dir = Path(data['assignment_dir'])
    output = assignment_dir / 'results' / 'mage_mapping_qc_result.txt'
    output.write_text(
        '\n'.join(
            [
                f"sra_run={data['sra_run']}",
                f"mapped_percent={data['mapped_percent']:.2f}",
                f"threshold={data['threshold']:.2f}",
                f"status={data['status']}",
                f"pipeline_returncode={data['returncode']}",
                f"mage_log={data['mage_log']}",
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    return {'mage_result': str(output)}
