import importlib.util
from pathlib import Path

import pandas as pd

from sipan import config

from .conftest import ANNEX_C

ROOT = Path(__file__).resolve().parent.parent


def _generator():
    spec = importlib.util.spec_from_file_location("generate_synthetic", ROOT / "scripts" / "generate_synthetic.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generation_is_deterministic():
    gen = _generator()
    pd.testing.assert_frame_equal(gen.generate(100, seed=7), gen.generate(100, seed=7))


def test_schema_matches_annex_a(trained_artifacts):
    df = pd.read_csv(trained_artifacts["dataset"])
    expected = {"id", "mensaje", *config.LABELS, "fuente", "grupo_similitud", "revision"}
    assert set(df.columns) == expected
    assert df["id"].is_unique and df["mensaje"].is_unique
    assert set(df["fuente"]) == {"sintetico"}
    assert df["grupo_similitud"].nunique() == 5
    assert df[list(config.LABELS)].isin([0, 1]).all().all()


def test_label_balance(trained_artifacts):
    df = pd.read_csv(trained_artifacts["dataset"])
    positives = df[list(config.LABELS)].mean()
    assert (positives > 0.1).all(), positives
    no_signal = (df[list(config.LABELS)].sum(axis=1) == 0).mean()
    assert 0.25 < no_signal < 0.6


def test_families_do_not_share_phrasings():
    gen = _generator()
    for pool in gen.POOLS.values():
        families = [gen._family_pool(pool, f) for f in range(gen.N_FAMILIES)]
        flat = [p for fam in families for p in fam]
        assert len(flat) == len(set(flat)) == len(pool)


def test_annex_c_examples_not_in_training_data():
    df = pd.read_csv(config.DATASET_PATH)
    for text in ANNEX_C.values():
        assert text not in set(df["mensaje"])


def test_committed_dataset_has_no_raw_identifiers():
    from sipan.preprocessing import anonymize

    df = pd.read_csv(config.DATASET_PATH)
    leaked = [m for m in df["mensaje"] if anonymize(m).found_identifiers]
    assert not leaked, leaked[:3]
