with open("src/aho/acceptance.py", "r") as f:
    code = f.read()

# 1. Replace dataclass with BaseModel
old_imports = "from dataclasses import dataclass, asdict\nfrom pathlib import Path"
new_imports = "from typing import Any\nfrom pydantic import BaseModel, model_validator\nfrom pathlib import Path"
code = code.replace(old_imports, new_imports)

old_class = """@dataclass
class AcceptanceResult:
    check_name: str
    passed: bool
    actual_exit: int
    actual_output: str
    matched: bool | None
    duration_seconds: float
    error: str | None = None"""

new_class = """class AcceptanceResult(BaseModel):
    check_name: str
    passed: bool
    actual_exit: int
    actual_output: str
    matched: bool | None
    duration_seconds: float
    error: str | None = None

    def __init__(self, *args, **kwargs):
        if args:
            fields = ["check_name", "passed", "actual_exit", "actual_output", "matched", "duration_seconds", "error"]
            for i, arg in enumerate(args):
                if i < len(fields):
                    kwargs[fields[i]] = arg
        super().__init__(**kwargs)

    @model_validator(mode="before")
    @classmethod
    def normalize_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "check_name" not in data and "name" in data:
                data["check_name"] = data.pop("name")
        return data"""
code = code.replace(old_class, new_class)

# 2. Update serialize_results
old_serialize = """def serialize_results(results: list[AcceptanceResult], path: str | Path) -> None:
    \"\"\"Write AcceptanceResult list to JSON file.\"\"\"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(r) for r in results]"""

new_serialize = """def serialize_results(results: list[AcceptanceResult], path: str | Path) -> None:
    \"\"\"Write AcceptanceResult list to JSON file.\"\"\"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = [r.model_dump() for r in results]"""
code = code.replace(old_serialize, new_serialize)

with open("src/aho/acceptance.py", "w") as f:
    f.write(code)
