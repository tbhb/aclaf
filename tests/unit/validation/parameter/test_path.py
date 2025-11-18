"""Unit tests for path parameter validators."""

from pathlib import Path

from aclaf.validation.parameter._path import (
    HasExtensions,
    IsDirectory,
    IsExecutable,
    IsFile,
    IsReadable,
    IsWritable,
    PathExists,
    validate_has_extensions,
    validate_is_directory,
    validate_is_executable,
    validate_is_file,
    validate_is_readable,
    validate_is_writable,
    validate_path_exists,
)


class TestValidatePathExists:
    def test_validates_existing_file(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = PathExists()

        result = validate_path_exists(str(test_file), metadata)

        assert result is None

    def test_validates_existing_directory(self, tmp_path: Path):
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        metadata = PathExists()

        result = validate_path_exists(str(test_dir), metadata)

        assert result is None

    def test_validates_path_object(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = PathExists()

        result = validate_path_exists(test_file, metadata)

        assert result is None

    def test_returns_error_for_nonexistent_path(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist.txt"
        metadata = PathExists()

        result = validate_path_exists(str(nonexistent), metadata)

        assert result is not None
        assert len(result) == 1
        assert "does not exist" in result[0]

    def test_handles_string_path(self, tmp_path: Path):
        metadata = PathExists()

        result = validate_path_exists(str(tmp_path), metadata)

        assert result is None


class TestValidateIsFile:
    def test_validates_file(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = IsFile()

        result = validate_is_file(str(test_file), metadata)

        assert result is None

    def test_returns_error_for_directory(self, tmp_path: Path):
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        metadata = IsFile()

        result = validate_is_file(str(test_dir), metadata)

        assert result is not None
        assert len(result) == 1
        assert "is not a file" in result[0]

    def test_validates_path_object(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = IsFile()

        result = validate_is_file(test_file, metadata)

        assert result is None

    def test_returns_error_for_nonexistent(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist.txt"
        metadata = IsFile()

        result = validate_is_file(str(nonexistent), metadata)

        assert result is not None
        assert len(result) == 1
        assert "does not exist" in result[0]


class TestValidateIsDirectory:
    def test_validates_directory(self, tmp_path: Path):
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        metadata = IsDirectory()

        result = validate_is_directory(str(test_dir), metadata)

        assert result is None

    def test_returns_error_for_file(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = IsDirectory()

        result = validate_is_directory(str(test_file), metadata)

        assert result is not None
        assert len(result) == 1
        assert "is not a directory" in result[0]

    def test_validates_path_object(self, tmp_path: Path):
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        metadata = IsDirectory()

        result = validate_is_directory(test_dir, metadata)

        assert result is None

    def test_returns_error_for_nonexistent(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist"
        metadata = IsDirectory()

        result = validate_is_directory(str(nonexistent), metadata)

        assert result is not None
        assert len(result) == 1
        assert "does not exist" in result[0]


class TestValidateIsReadable:
    def test_validates_readable_file(self, tmp_path: Path):
        test_file = tmp_path / "readable.txt"
        _ = test_file.write_text("content")
        metadata = IsReadable()

        result = validate_is_readable(str(test_file), metadata)

        assert result is None

    def test_validates_readable_directory(self, tmp_path: Path):
        test_dir = tmp_path / "readable_dir"
        test_dir.mkdir()
        metadata = IsReadable()

        result = validate_is_readable(str(test_dir), metadata)

        assert result is None

    def test_validates_path_object(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = IsReadable()

        result = validate_is_readable(test_file, metadata)

        assert result is None

    def test_returns_error_for_nonexistent(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist.txt"
        metadata = IsReadable()

        result = validate_is_readable(str(nonexistent), metadata)

        assert result is not None
        assert len(result) == 1
        assert "does not exist" in result[0]


class TestValidateIsWritable:
    def test_validates_writable_file(self, tmp_path: Path):
        test_file = tmp_path / "writable.txt"
        _ = test_file.write_text("content")
        metadata = IsWritable()

        result = validate_is_writable(str(test_file), metadata)

        assert result is None

    def test_validates_writable_directory(self, tmp_path: Path):
        test_dir = tmp_path / "writable_dir"
        test_dir.mkdir()
        metadata = IsWritable()

        result = validate_is_writable(str(test_dir), metadata)

        assert result is None

    def test_validates_path_object(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = IsWritable()

        result = validate_is_writable(test_file, metadata)

        assert result is None

    def test_returns_error_for_nonexistent(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist.txt"
        metadata = IsWritable()

        result = validate_is_writable(str(nonexistent), metadata)

        assert result is not None
        assert len(result) == 1
        assert "does not exist" in result[0]


class TestValidateIsExecutable:
    def test_validates_executable_file(self, tmp_path: Path):
        test_file = tmp_path / "executable.sh"
        _ = test_file.write_text("#!/bin/bash\necho hello")
        test_file.chmod(0o755)
        metadata = IsExecutable()

        result = validate_is_executable(str(test_file), metadata)

        assert result is None

    def test_returns_error_for_non_executable(self, tmp_path: Path):
        test_file = tmp_path / "not_executable.txt"
        _ = test_file.write_text("content")
        test_file.chmod(0o644)
        metadata = IsExecutable()

        result = validate_is_executable(str(test_file), metadata)

        assert result is not None
        assert len(result) == 1
        assert "is not executable" in result[0]

    def test_validates_path_object(self, tmp_path: Path):
        test_file = tmp_path / "executable.sh"
        _ = test_file.write_text("#!/bin/bash")
        test_file.chmod(0o755)
        metadata = IsExecutable()

        result = validate_is_executable(test_file, metadata)

        assert result is None

    def test_returns_error_for_nonexistent(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist.sh"
        metadata = IsExecutable()

        result = validate_is_executable(str(nonexistent), metadata)

        assert result is not None
        assert len(result) == 1
        assert "does not exist" in result[0]


class TestValidateHasExtensions:
    def test_validates_file_with_single_extension(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = HasExtensions(extensions=".txt")

        result = validate_has_extensions(str(test_file), metadata)

        assert result is None

    def test_validates_file_with_multiple_extensions(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = HasExtensions(extensions=[".txt", ".md"])

        result = validate_has_extensions(str(test_file), metadata)

        assert result is None

    def test_returns_error_for_wrong_extension(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        _ = test_file.write_text("content")
        metadata = HasExtensions(extensions=".md")

        result = validate_has_extensions(str(test_file), metadata)

        assert result is not None
        assert len(result) == 1
        assert "must have one of these extensions" in result[0]

    def test_validates_path_object(self, tmp_path: Path):
        test_file = tmp_path / "test.py"
        _ = test_file.write_text("print('hello')")
        metadata = HasExtensions(extensions=".py")

        result = validate_has_extensions(test_file, metadata)

        assert result is None

    def test_returns_error_for_no_extension(self, tmp_path: Path):
        test_file = tmp_path / "noext"
        _ = test_file.write_text("content")
        metadata = HasExtensions(extensions=".txt")

        result = validate_has_extensions(str(test_file), metadata)

        assert result is not None
        assert len(result) == 1
        assert "must have one of these extensions" in result[0]

    def test_validates_file_with_case_sensitive_extension(self, tmp_path: Path):
        test_file = tmp_path / "test.TXT"
        _ = test_file.write_text("content")
        metadata = HasExtensions(extensions=".TXT")

        result = validate_has_extensions(str(test_file), metadata)

        assert result is None

    def test_validates_file_with_compound_extension(self, tmp_path: Path):
        test_file = tmp_path / "archive.tar.gz"
        _ = test_file.write_text("content")
        metadata = HasExtensions(extensions=".tar.gz")

        result = validate_has_extensions(str(test_file), metadata)

        assert result is None
