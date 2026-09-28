[project]
name = "analogsensor"
version = "0.1.0"
docker ="softmastergeo/analogsensor"
description = "BlueOS extension for analog sensor input"
keywords = ["blueos", "raspberrypi", "ads1115", "sensors"]


[project.optional-dependencies]
dev = [
    "black==22.3.0",
    "isort==5.10.1",
    "mypy==1.15.0",
    "pydantic==1.9.0",
    "pylint==3.3.7",
    "types-Markdown==3.6.0.20240316",
]

[tool.setuptools]
packages = [
  "blueos_repository",
  "blueos_repository.docker",
  "blueos_repository.extension"
]

[tool.black]
line-length = 120

[tool.isort]
profile = "black"

[tool.pylint.master]
enable = "all"
disable = [
    "broad-exception-raised",
    "line-too-long", # We already have this in black.
    "locally-disabled", # We know what we are doing, necessary to load plugins in runtime
    "missing-class-docstring",
    "missing-function-docstring",
    "missing-module-docstring",
    "suppressed-message",
    "wrong-import-position",
]

[tool.pylint.miscellaneous]
notes = ["FIXME"] # TODO is removed for internal development

[tool.mypy]
allow_untyped_decorators = true
disallow_subclassing_any = false
ignore_missing_imports = true
strict = true
warn_unreachable = true
warn_unused_ignores = false