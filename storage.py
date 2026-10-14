import json
from pathlib import Path
from typing import Dict, TypeVar, Callable, List
from models import Book

T = TypeVar("T")


# Общий шаблон загрузки списка объектов и построения словаря по ключу
def _load_list_to_dict(
        path: Path, item_from_dict: Callable[[dict], T], key_extractor: Callable[[dict], str]
) -> Dict[str, T]:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return {}
    except OSError:
        return {}

    result: Dict[str, T] = {}
    for item_raw in data:
        try:
            key = key_extractor(item_raw)
            obj = item_from_dict(item_raw)
            result[key] = obj
        except (KeyError, TypeError, ValueError):
            continue
    return result


# Общий шаблон сохранения словаря как списка объектов
def _save_dict_as_list(path: Path, data: Dict[str, T], item_to_dict: Callable[[T], dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized: List[dict] = [item_to_dict(v) for v in data.values()]
    with path.open("w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)


def load_books(path: Path) -> Dict[str, Book]:
    return _load_list_to_dict(path, item_from_dict=Book.from_dict, key_extractor=lambda r: r["name"])


def save_books(path: Path, data: Dict[str, Book]):
    _save_dict_as_list(path, data, item_to_dict=lambda r: r.to_dict())
