import os
import json


def load_json(json_path):
    # Check file existence
    if not os.path.isfile(json_path):
        raise RuntimeError(f"File not found: {json_path}")
    # Load file content
    with open(json_path) as json_file:
        return json.load(json_file)


def write_json(out_json_path, data):
    # Ensure parent directory existence
    out_dir = os.path.dirname(os.path.abspath(out_json_path))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    # Write file content
    with open(out_json_path, "w") as f_out:
        json.dump(data, f_out, indent=3)


def get_kib_size_as_human_readable_str(value_kib):
    # By default, commands such as df display the amount of memory in kibibytes
    if value_kib is None:
        return str(value_kib)
    # -- KiB
    if value_kib < 1024:
        return f"{value_kib:.0f}K"
    # -- MiB
    value_mib = value_kib / 1024
    if value_mib < 10:
        return f"{value_mib:.1f}M"
    if value_mib < 1024:
        return f"{value_mib:.0f}M"
    # -- GiB
    value_gib = value_mib / 1024
    if value_gib < 10:
        return f"{value_gib:.1f}G"
    if value_gib < 1024:
        return f"{value_gib:.0f}G"
    # -- TiB
    value_tib = value_gib / 1024
    if value_tib < 10:
        return f"{value_tib:.1f}T"
    if value_tib < 1024:
        return f"{value_tib:.0f}T"
    # -- PiB
    value_pib = value_tib / 1024
    if value_pib < 10:
        return f"{value_pib:.1f}P"
    if value_pib < 1024:
        return f"{value_pib:.0f}P"

