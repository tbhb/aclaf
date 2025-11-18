"""Unit tests for sequence parameter validators."""

from aclaf.validation.parameter._sequence import (
    AllMatch,
    AnyMatch,
    ItemType,
    NoneMatch,
    SequenceContains,
    UniqueItems,
    validate_all_match,
    validate_any_match,
    validate_item_type,
    validate_none_match,
    validate_sequence_contains,
    validate_unique_items,
)


class TestUniqueItems:
    def test_validates_unique_list(self):
        metadata = UniqueItems()
        value = [1, 2, 3, 4]

        result = validate_unique_items(value, metadata)

        assert result is None

    def test_validates_empty_list(self):
        metadata = UniqueItems()
        value = []

        result = validate_unique_items(value, metadata)

        assert result is None

    def test_validates_single_item_list(self):
        metadata = UniqueItems()
        value = [1]

        result = validate_unique_items(value, metadata)

        assert result is None

    def test_rejects_duplicate_integers(self):
        metadata = UniqueItems()
        value = [1, 2, 2, 3]

        result = validate_unique_items(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "contains duplicate items" in result[0]
        assert "2" in result[0]

    def test_rejects_duplicate_strings(self):
        metadata = UniqueItems()
        value = ["a", "b", "a", "c"]

        result = validate_unique_items(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "contains duplicate items" in result[0]
        assert "'a'" in result[0]

    def test_rejects_multiple_duplicates(self):
        metadata = UniqueItems()
        value = [1, 2, 2, 3, 3]

        result = validate_unique_items(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "2" in result[0]
        assert "3" in result[0]

    def test_validates_unique_tuple(self):
        metadata = UniqueItems()
        value = (1, 2, 3)

        result = validate_unique_items(value, metadata)

        assert result is None

    def test_rejects_set_as_non_sequence(self):
        metadata = UniqueItems()
        # Sets are not Sequences in the ABC sense
        value = {1, 2, 3}

        result = validate_unique_items(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]

    def test_rejects_string_as_sequence(self):
        metadata = UniqueItems()
        value = "abc"

        result = validate_unique_items(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]

    def test_validates_none_value(self):
        metadata = UniqueItems()
        value = None

        result = validate_unique_items(value, metadata)

        assert result is None

    def test_rejects_non_sequence_value(self):
        metadata = UniqueItems()
        value = 42

        result = validate_unique_items(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]

    def test_handles_unhashable_items(self):
        metadata = UniqueItems()
        value = [[1, 2], [3, 4], [1, 2]]

        result = validate_unique_items(value, metadata)

        assert result is not None
        assert "contains duplicate items" in result[0]


class TestSequenceContains:
    def test_validates_sequence_containing_item(self):
        metadata = SequenceContains(items=("a",))
        value = ["a", "b", "c"]

        result = validate_sequence_contains(value, metadata)

        assert result is None

    def test_validates_sequence_containing_all_items(self):
        metadata = SequenceContains(items=("a", "b"))
        value = ["a", "b", "c"]

        result = validate_sequence_contains(value, metadata)

        assert result is None

    def test_rejects_sequence_missing_item(self):
        metadata = SequenceContains(items=("d",))
        value = ["a", "b", "c"]

        result = validate_sequence_contains(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must contain" in result[0]
        assert "'d'" in result[0]

    def test_rejects_sequence_missing_multiple_items(self):
        metadata = SequenceContains(items=("d", "e"))
        value = ["a", "b", "c"]

        result = validate_sequence_contains(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'d'" in result[0]
        assert "'e'" in result[0]

    def test_validates_empty_required_items(self):
        metadata = SequenceContains(items=())
        value = ["a", "b", "c"]

        result = validate_sequence_contains(value, metadata)

        assert result is None

    def test_validates_none_value(self):
        metadata = SequenceContains(items=("a",))
        value = None

        result = validate_sequence_contains(value, metadata)

        assert result is None

    def test_rejects_non_sequence_value(self):
        metadata = SequenceContains(items=("a",))
        value = 42

        result = validate_sequence_contains(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]

    def test_rejects_string_as_sequence(self):
        metadata = SequenceContains(items=("a",))
        value = "abc"

        result = validate_sequence_contains(value, metadata)

        assert result is not None


class TestAllMatch:
    def test_validates_all_items_match(self):
        metadata = AllMatch(predicate=lambda x: x > 0)
        value = [1, 2, 3, 4]

        result = validate_all_match(value, metadata)

        assert result is None

    def test_validates_empty_sequence(self):
        metadata = AllMatch(predicate=lambda x: x > 0)
        value = []

        result = validate_all_match(value, metadata)

        assert result is None

    def test_rejects_one_item_not_matching(self):
        metadata = AllMatch(predicate=lambda x: x > 0)
        value = [1, 2, -1, 3]

        result = validate_all_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "do not match predicate" in result[0]
        assert "-1" in result[0]

    def test_rejects_multiple_items_not_matching(self):
        metadata = AllMatch(predicate=lambda x: x > 0)
        value = [1, -1, -2, 3]

        result = validate_all_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "do not match predicate" in result[0]

    def test_limits_error_message_to_five_items(self):
        metadata = AllMatch(predicate=lambda x: x > 0)
        value = [-1, -2, -3, -4, -5, -6, -7]

        result = validate_all_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "7 items do not match" in result[0]
        assert "First 5:" in result[0]

    def test_validates_none_value(self):
        metadata = AllMatch(predicate=lambda x: x > 0)
        value = None

        result = validate_all_match(value, metadata)

        assert result is None

    def test_rejects_non_sequence_value(self):
        metadata = AllMatch(predicate=lambda x: x > 0)
        value = 42

        result = validate_all_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]


class TestAnyMatch:
    def test_validates_one_item_matches(self):
        metadata = AnyMatch(predicate=lambda x: x > 10)
        value = [1, 2, 15, 3]

        result = validate_any_match(value, metadata)

        assert result is None

    def test_validates_all_items_match(self):
        metadata = AnyMatch(predicate=lambda x: x > 0)
        value = [1, 2, 3, 4]

        result = validate_any_match(value, metadata)

        assert result is None

    def test_rejects_no_items_matching(self):
        metadata = AnyMatch(predicate=lambda x: x > 10)
        value = [1, 2, 3, 4]

        result = validate_any_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "at least one item must match predicate" in result[0]

    def test_rejects_empty_sequence(self):
        metadata = AnyMatch(predicate=lambda x: x > 0)
        value = []

        result = validate_any_match(value, metadata)

        assert result is not None

    def test_validates_none_value(self):
        metadata = AnyMatch(predicate=lambda x: x > 0)
        value = None

        result = validate_any_match(value, metadata)

        assert result is None

    def test_rejects_non_sequence_value(self):
        metadata = AnyMatch(predicate=lambda x: x > 0)
        value = 42

        result = validate_any_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]


class TestNoneMatch:
    def test_validates_no_items_match(self):
        metadata = NoneMatch(predicate=lambda x: x < 0)
        value = [1, 2, 3, 4]

        result = validate_none_match(value, metadata)

        assert result is None

    def test_validates_empty_sequence(self):
        metadata = NoneMatch(predicate=lambda x: x < 0)
        value = []

        result = validate_none_match(value, metadata)

        assert result is None

    def test_rejects_one_item_matching(self):
        metadata = NoneMatch(predicate=lambda x: x < 0)
        value = [1, 2, -1, 3]

        result = validate_none_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must not match predicate" in result[0]
        assert "-1" in result[0]

    def test_rejects_all_items_matching(self):
        metadata = NoneMatch(predicate=lambda x: x > 0)
        value = [1, 2, 3, 4]

        result = validate_none_match(value, metadata)

        assert result is not None

    def test_limits_error_message_to_five_items(self):
        metadata = NoneMatch(predicate=lambda x: x > 0)
        value = [1, 2, 3, 4, 5, 6, 7]

        result = validate_none_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "7 items match" in result[0]
        assert "First 5:" in result[0]

    def test_validates_none_value(self):
        metadata = NoneMatch(predicate=lambda x: x < 0)
        value = None

        result = validate_none_match(value, metadata)

        assert result is None

    def test_rejects_non_sequence_value(self):
        metadata = NoneMatch(predicate=lambda x: x < 0)
        value = 42

        result = validate_none_match(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]


class TestItemType:
    def test_validates_all_items_correct_type(self):
        metadata = ItemType(types=(int,))
        value = [1, 2, 3, 4]

        result = validate_item_type(value, metadata)

        assert result is None

    def test_validates_multiple_allowed_types(self):
        metadata = ItemType(types=(int, str))
        value = [1, "a", 2, "b"]

        result = validate_item_type(value, metadata)

        assert result is None

    def test_validates_empty_sequence(self):
        metadata = ItemType(types=(int,))
        value = []

        result = validate_item_type(value, metadata)

        assert result is None

    def test_rejects_one_wrong_type(self):
        metadata = ItemType(types=(int,))
        value = [1, 2, "three", 4]

        result = validate_item_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be of type int" in result[0]
        assert "'three' (str)" in result[0]

    def test_rejects_multiple_wrong_types(self):
        metadata = ItemType(types=(int,))
        value = [1, "two", "three", 4]

        result = validate_item_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "'two' (str)" in result[0]
        assert "'three' (str)" in result[0]

    def test_limits_error_message_to_five_items(self):
        metadata = ItemType(types=(int,))
        value = ["a", "b", "c", "d", "e", "f", "g"]

        result = validate_item_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "7 items are not of type" in result[0]
        assert "First 5:" in result[0]

    def test_validates_none_value(self):
        metadata = ItemType(types=(int,))
        value = None

        result = validate_item_type(value, metadata)

        assert result is None

    def test_rejects_non_sequence_value(self):
        metadata = ItemType(types=(int,))
        value = 42

        result = validate_item_type(value, metadata)

        assert result is not None
        assert len(result) == 1
        assert "must be a sequence" in result[0]

    def test_rejects_string_as_sequence(self):
        metadata = ItemType(types=(str,))
        value = "abc"

        result = validate_item_type(value, metadata)

        assert result is not None
