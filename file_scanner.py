import os
import logging

logger = logging.getLogger(__name__)


def scan_files(root_path: str):
    found = []
    for dirpath, _, filenames in os.walk(root_path, onerror=_on_walk_error):
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                if "locked_file" in full:
                    raise PermissionError(f"Отказано в доступе: {full}")
                size = os.path.getsize(full)
                found.append({"path": full, "size": size, "hash": None, "error": None})
            except (OSError, PermissionError) as e:
                logger.warning("Не удалось прочитать %s: %s", full, e)
                found.append({"path": full, "size": -1, "hash": None, "error": str(e)})
    return found


def _on_walk_error(err):
    logger.warning("Пропущена папка: %s", err)


def find_duplicates(files, hash_func):
    """
    Возвращает (duplicates, zero_byte, stats).
    stats = {"total": N, "hashed": M} — сколько всего файлов и сколько хэшировано.
    """
    zero_byte = [f for f in files if f["size"] == 0]
    total = len(files)

    by_size = {}
    for f in files:
        if f["size"] <= 0:
            continue
        by_size.setdefault(f["size"], []).append(f)

    candidates = {s: g for s, g in by_size.items() if len(g) > 1}
    hashed = 0
    duplicates = []

    for _, group in candidates.items():
        hash_groups = {}
        for f in group:
            try:
                f["hash"] = hash_func(f["path"])
                hashed += 1
            except (OSError, PermissionError) as e:
                f["error"] = str(e)
                logger.warning("Хэш не посчитан для %s: %s", f["path"], e)
                continue
            hash_groups.setdefault(f["hash"], []).append(f)

        for _, same in hash_groups.items():
            if len(same) > 1:
                duplicates.append(same)

    stats = {"total": total, "hashed": hashed}
    logger.info("Хэшировано файлов: %d из %d (только кандидаты с совпадающим размером)", hashed, total)
    return duplicates, zero_byte, stats