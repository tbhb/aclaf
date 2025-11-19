from aclaf.exceptions import AclafError


class TestAclafError:
    def test_default(self):
        error = AclafError()
        assert str(error) == "An unexpected error occurred."
