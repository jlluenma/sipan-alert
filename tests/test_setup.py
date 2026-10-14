from sipan import config


def test_labels_match_annex_a():
    assert config.LABELS == (
        "pago_anticipado",
        "acceso_invasivo",
        "amenaza_presion",
        "condiciones_opacas",
    )


def test_paths_live_inside_project():
    for path in (config.DATASET_PATH, config.MODEL_PATH, config.METRICS_PATH):
        assert config.ROOT in path.parents


def test_core_dependencies_import():
    import joblib  # noqa: F401
    import numpy  # noqa: F401
    import pandas  # noqa: F401
    import sklearn  # noqa: F401
    import streamlit  # noqa: F401
