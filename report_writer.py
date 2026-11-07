import json


def write_report(path, duplicates, zero_byte, errors, stats):
    data = {
        "duplicates": [
            [{"path": f["path"], "size": f["size"], "hash": f["hash"]} for f in group]
            for group in duplicates
        ],
        "empty_files": [f["path"] for f in zero_byte],
        "access_errors": [{"path": f["path"], "error": f["error"]}
                          for f in errors if f.get("error")],
        "stats": {
            "total_files": stats["total"],
            "hashed_files": stats["hashed"],
            "duplicate_groups": len(duplicates),
            "empty_files": len(zero_byte),
            "access_errors": sum(1 for f in errors if f.get("error")),
        },
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)