import pytest

from apps.accounts.models import User
from tests.factories import UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = UserFactory(role='ANALYST')
        assert user.pk is not None
        assert user.is_analyst

    def test_role_properties(self):
        analyst = UserFactory(role='ANALYST')
        accountant = UserFactory(role='ACCOUNTANT')
        director = UserFactory(role='DIRECTOR')
        client_user = UserFactory(role='CLIENT_USER', is_portal_user=True)

        assert analyst.is_analyst
        assert not analyst.is_accountant
        assert accountant.is_accountant
        assert director.is_director
        assert client_user.is_client_user
        assert client_user.is_portal_user

    def test_str_method(self):
        user = UserFactory(first_name='علی', last_name='احمدی')
        assert 'علی' in str(user)
