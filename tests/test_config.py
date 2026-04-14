import newspull.config as config_module


def test_load_prefs_creates_default_when_missing(tmp_prefs_path):
    prefs = config_module.load_prefs()
    assert "topics" in prefs
    assert "sources" in prefs
    assert "credibility" in prefs
    assert "digester" in prefs
    assert tmp_prefs_path.exists()


def test_save_and_reload_prefs(tmp_prefs_path):
    prefs = config_module.load_prefs()
    prefs["topics"]["ai"] = 0.5
    config_module.save_prefs(prefs)
    reloaded = config_module.load_prefs()
    assert reloaded["topics"]["ai"] == 0.5


def test_save_creates_backup(tmp_prefs_path):
    config_module.load_prefs()  # creates file
    config_module.save_prefs(config_module.load_prefs())
    bak = tmp_prefs_path.with_suffix(".toml.bak")
    assert bak.exists()


def test_restore_backup(tmp_prefs_path):
    prefs = config_module.load_prefs()
    original_ai_weight = prefs["topics"]["ai"]
    config_module.save_prefs(prefs)  # creates backup of original

    # Corrupt the current prefs
    prefs["topics"]["ai"] = 0.0
    config_module.save_prefs(prefs)

    config_module.restore_prefs_backup()
    restored = config_module.load_prefs()
    assert restored["topics"]["ai"] == original_ai_weight


def test_default_prefs_structure(tmp_prefs_path):
    prefs = config_module.load_prefs()
    assert isinstance(prefs["topics"], dict)
    assert isinstance(prefs["sources"]["reddit"], list)
    assert isinstance(prefs["credibility"]["min_score"], float)
    assert isinstance(prefs["digester"]["keypoints"], int)
