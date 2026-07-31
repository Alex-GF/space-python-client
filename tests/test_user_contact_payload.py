from __future__ import annotations

from space_client.types import UserContact


def test_an_unset_optional_field_is_omitted_rather_than_null():
    """Space accepts a missing key and refuses an explicit null.

    ``UserContact`` declares ``email`` and ``phone`` as optional with a default
    of ``None``, but serialised them as ``null`` - so a contact built from the
    defaults was refused:

        422 {"error":"The userContact.phone field must be a string"}

    Verified against SPACE 1.0.0: the same contract is created (201) with the
    field omitted.
    """
    payload = UserContact(user_id="u1", username="u1").to_dict()

    assert "phone" not in payload
    assert "email" not in payload


def test_a_field_that_was_set_is_still_sent():
    payload = UserContact(
        user_id="u1", username="u1", email="a@b.org", phone="+34600000000"
    ).to_dict()

    assert payload["email"] == "a@b.org"
    assert payload["phone"] == "+34600000000"


def test_an_empty_string_is_a_value_and_survives():
    # "" is something the caller chose to send; only None means "not provided".
    payload = UserContact(user_id="u1", username="u1", phone="").to_dict()

    assert payload["phone"] == ""


def test_the_required_fields_are_always_present():
    payload = UserContact(user_id="u1", username="u1").to_dict()

    assert payload["userId"] == "u1"
    assert payload["username"] == "u1"
    assert payload["firstName"] == ""
    assert payload["lastName"] == ""


def test_a_contact_round_trips_through_the_wire_shape():
    original = UserContact(user_id="u1", username="u1", email="a@b.org")

    restored = UserContact.from_dict(original.to_dict())

    assert restored.email == "a@b.org"
    assert restored.phone is None
