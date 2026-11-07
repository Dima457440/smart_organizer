import os
import logging

logger = logging.getLogger(__name__)


def safe_delete(selected_paths, duplicates_groups, dry_run=False):
    group_of = {}
    for idx, group in enumerate(duplicates_groups):
        for f in group:
            group_of[f["path"]] = idx

    deleted, failed, protected = [], [], []
    
    # Считаем, сколько файлов выделено из каждой группы
    selected_counts = {}
    for p in selected_paths:
        gidx = group_of.get(p)
        if gidx is not None:
            selected_counts[gidx] = selected_counts.get(gidx, 0) + 1

    # Запоминаем, какой файл мы защитим в каждой группе (если выделены все)
    protected_in_group = {}
    for gidx, count in selected_counts.items():
        if count >= len(duplicates_groups[gidx]):
            # Выделены все — защищаем первый файл из этой группы
            protected_in_group[gidx] = duplicates_groups[gidx][0]["path"]

    for path in selected_paths:
        gidx = group_of.get(path)
        
        # Если этот файл выбран как "жертва" для защиты, пропускаем его
        if gidx is not None and protected_in_group.get(gidx) == path:
            protected.append(path)
            logger.warning("Защищён от удаления (последний в группе): %s", path)
            continue

        try:
            if not dry_run:
                os.remove(path)
            deleted.append(path)
            logger.info("Удалён: %s", path)
        except OSError as e:
            failed.append((path, str(e)))
            logger.error("Не удалось удалить %s: %s", path, e)

    return deleted, failed, protected
