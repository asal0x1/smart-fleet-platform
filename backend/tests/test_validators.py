"""Telefon va koordinata validatorlari (unit — DB kerak emas)."""
import pytest
from rest_framework import serializers

from apps.common.validators import (
    LatitudeField,
    LongitudeField,
    PhoneField,
    normalize_phone,
    validate_phone,
)


class TestNormalizePhone:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("+998901234567", "+998901234567"),
            ("998901234567", "+998901234567"),
            ("901234567", "+998901234567"),
            ("+998 90 123-45-67", "+998901234567"),
            ("(998) 90 123 45 67", "+998901234567"),
        ],
    )
    def test_turli_formatlar_bir_xil_natija(self, raw, expected):
        assert normalize_phone(raw) == expected

    def test_bosh_qiymat(self):
        assert normalize_phone("") == ""
        assert normalize_phone(None) is None


class TestValidatePhone:
    def test_togri_raqam(self):
        assert validate_phone("901234567") == "+998901234567"

    @pytest.mark.parametrize(
        "bad",
        ["12345", "+7999123456", "+9989012345678", "+99890123456", "abcdefghij"],
    )
    def test_notogri_raqam_rad_etiladi(self, bad):
        with pytest.raises(serializers.ValidationError):
            validate_phone(bad)


class TestPhoneField:
    def test_serializerda_normalizatsiya(self):
        class S(serializers.Serializer):
            phone = PhoneField()

        s = S(data={"phone": "90 123 45 67"})
        assert s.is_valid(), s.errors
        assert s.validated_data["phone"] == "+998901234567"

    def test_serializerda_xato(self):
        class S(serializers.Serializer):
            phone = PhoneField()

        s = S(data={"phone": "123"})
        assert not s.is_valid()
        assert "phone" in s.errors


class TestKoordinatalar:
    @pytest.mark.parametrize("lat,ok", [(-90, True), (0, True), (90, True),
                                        (90.1, False), (-91, False), (999, False)])
    def test_latitude_chegaralari(self, lat, ok):
        class S(serializers.Serializer):
            lat = LatitudeField()

        assert S(data={"lat": lat}).is_valid() is ok

    @pytest.mark.parametrize("lng,ok", [(-180, True), (69.24, True), (180, True),
                                        (180.5, False), (-500, False)])
    def test_longitude_chegaralari(self, lng, ok):
        class S(serializers.Serializer):
            lng = LongitudeField()

        assert S(data={"lng": lng}).is_valid() is ok
