"""Unit tests for command dependency validators."""

from aclaf.validation.command import (
    Forbids,
    Requires,
    validate_forbids,
    validate_requires,
)


class TestRequires:
    def test_validates_source_not_provided(self):
        metadata = Requires(source="ssl", required=("cert", "key"))
        value = {"ssl": None, "cert": None, "key": None}

        result = validate_requires(value, metadata)

        assert result is None

    def test_validates_source_missing_from_mapping(self):
        metadata = Requires(source="ssl", required=("cert", "key"))
        value = {"cert": "cert.pem", "key": "key.pem"}

        result = validate_requires(value, metadata)

        assert result is None

    def test_validates_source_provided_with_all_required(self):
        metadata = Requires(source="ssl", required=("cert", "key"))
        value = {"ssl": True, "cert": "cert.pem", "key": "key.pem"}

        result = validate_requires(value, metadata)

        assert result is None

    def test_rejects_source_provided_missing_one_required(self):
        metadata = Requires(source="ssl", required=("cert", "key"))
        value = {"ssl": True, "cert": "cert.pem", "key": None}

        result = validate_requires(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "ssl" in result[0]
        assert "requires" in result[0]
        assert "'key'" in result[0]

    def test_rejects_source_provided_missing_all_required(self):
        metadata = Requires(source="ssl", required=("cert", "key"))
        value = {"ssl": True, "cert": None, "key": None}

        result = validate_requires(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'cert'" in result[0]
        assert "'key'" in result[0]

    def test_validates_source_provided_with_single_required(self):
        metadata = Requires(source="verbose", required=("log_file",))
        value = {"verbose": True, "log_file": "output.log"}

        result = validate_requires(value, metadata)

        assert result is None

    def test_rejects_source_provided_missing_single_required(self):
        metadata = Requires(source="verbose", required=("log_file",))
        value = {"verbose": True, "log_file": None}

        result = validate_requires(value, metadata)

        assert result is not None
        assert len(result) == 1

    def test_validates_empty_required_list(self):
        metadata = Requires(source="ssl", required=())
        value = {"ssl": True}

        result = validate_requires(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = Requires(source="ssl", required=("cert", "key"))
        value = "not a mapping"

        result = validate_requires(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "require parameter mapping" in result[0]

    def test_rejects_source_false_with_missing_required(self):
        metadata = Requires(source="ssl", required=("cert",))
        value = {"ssl": False, "cert": None}

        result = validate_requires(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'cert'" in result[0]

    def test_rejects_source_zero_with_missing_required(self):
        metadata = Requires(source="count", required=("file",))
        value = {"count": 0, "file": None}

        result = validate_requires(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'file'" in result[0]

    def test_rejects_source_empty_string_with_missing_required(self):
        metadata = Requires(source="name", required=("id",))
        value = {"name": "", "id": None}

        result = validate_requires(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'id'" in result[0]


class TestForbids:
    def test_validates_source_not_provided(self):
        metadata = Forbids(source="quiet", forbidden=("verbose", "debug"))
        value = {"quiet": None, "verbose": True, "debug": True}

        result = validate_forbids(value, metadata)

        assert result is None

    def test_validates_source_missing_from_mapping(self):
        metadata = Forbids(source="quiet", forbidden=("verbose", "debug"))
        value = {"verbose": True, "debug": True}

        result = validate_forbids(value, metadata)

        assert result is None

    def test_validates_source_provided_with_no_forbidden(self):
        metadata = Forbids(source="quiet", forbidden=("verbose", "debug"))
        value = {"quiet": True, "verbose": None, "debug": None}

        result = validate_forbids(value, metadata)

        assert result is None

    def test_rejects_source_provided_with_one_forbidden(self):
        metadata = Forbids(source="quiet", forbidden=("verbose", "debug"))
        value = {"quiet": True, "verbose": True, "debug": None}

        result = validate_forbids(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "quiet" in result[0]
        assert "forbids" in result[0]
        assert "'verbose'" in result[0]

    def test_rejects_source_provided_with_all_forbidden(self):
        metadata = Forbids(source="quiet", forbidden=("verbose", "debug"))
        value = {"quiet": True, "verbose": True, "debug": True}

        result = validate_forbids(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'verbose'" in result[0]
        assert "'debug'" in result[0]

    def test_validates_source_provided_with_single_forbidden_absent(self):
        metadata = Forbids(source="batch", forbidden=("interactive",))
        value = {"batch": True, "interactive": None}

        result = validate_forbids(value, metadata)

        assert result is None

    def test_rejects_source_provided_with_single_forbidden_present(self):
        metadata = Forbids(source="batch", forbidden=("interactive",))
        value = {"batch": True, "interactive": True}

        result = validate_forbids(value, metadata)

        assert result is not None
        assert len(result) == 1

    def test_validates_empty_forbidden_list(self):
        metadata = Forbids(source="quiet", forbidden=())
        value = {"quiet": True, "verbose": True}

        result = validate_forbids(value, metadata)

        assert result is None

    def test_rejects_non_mapping_value(self):
        metadata = Forbids(source="quiet", forbidden=("verbose",))
        value = 123

        result = validate_forbids(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "require parameter mapping" in result[0]

    def test_rejects_source_false_with_forbidden_present(self):
        metadata = Forbids(source="quiet", forbidden=("verbose",))
        value = {"quiet": False, "verbose": True}

        result = validate_forbids(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'verbose'" in result[0]

    def test_rejects_source_zero_with_forbidden_present(self):
        metadata = Forbids(source="count", forbidden=("all",))
        value = {"count": 0, "all": True}

        result = validate_forbids(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'all'" in result[0]
