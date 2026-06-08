from pathlib import Path

from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data(data, *args, **kwargs):
    result_path = Path(__file__).resolve().parents[2] / 'results' / 'mage_hello_world_result.txt'
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        f"{data['message']}\nframework={data['framework']}\nassignment={data['assignment']}\n",
        encoding='utf-8',
    )
    return {'result_path': str(result_path)}
