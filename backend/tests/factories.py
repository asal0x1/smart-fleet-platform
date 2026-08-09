"""factory-boy fabrikalari — testlarda ma'lumot yaratish uchun."""
import factory
from django.contrib.gis.geos import Point

from apps.drivers.models import Driver
from apps.orders.models import Order, OrderStatus, Review, ReviewKind, Tariff
from apps.payments.models import Payment, PaymentState
from apps.requests.models import HeavyEquipmentRequest, WeddingRequest
from apps.users.models import User, UserRole

TEST_PASSWORD = "TestParol123"

# Toshkent markazi atrofidagi nuqtalar
TASHKENT = (41.311081, 69.240562)


def point(lat, lng):
    return Point(lng, lat, srid=4326)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    phone = factory.Sequence(lambda n: f"+99890{n:07d}")
    full_name = factory.Sequence(lambda n: f"Foydalanuvchi {n}")
    role = UserRole.CLIENT
    is_active = True
    is_verified = True

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.set_password(extracted or TEST_PASSWORD)
        obj.save(update_fields=["password"])


class ClientFactory(UserFactory):
    role = UserRole.CLIENT


class DriverUserFactory(UserFactory):
    role = UserRole.DRIVER


class AdminFactory(UserFactory):
    role = UserRole.ADMIN
    is_staff = True


def test_image(name="doc.jpg"):
    """Kichik haqiqiy JPEG — ImageField validatsiyasidan o'tadi."""
    return factory.django.ImageField(filename=name, width=20, height=20)


class DriverFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Driver

    user = factory.SubFactory(DriverUserFactory)
    license_photo = test_image("license.jpg")
    tech_passport_photo = test_image("techpass.jpg")
    car_model = "Chevrolet Cobalt"
    car_color = "oq"
    car_number = factory.Sequence(lambda n: f"01A{n:03d}BC")
    license_number = factory.Sequence(lambda n: f"AA{n:07d}")
    is_active = True          # tasdiqlangan
    is_online = True
    location = factory.LazyFunction(lambda: point(*TASHKENT))


class UnapprovedDriverFactory(DriverFactory):
    """Hujjatlari to'liq, lekin admin hali tasdiqlamagan."""

    is_active = False
    is_online = False


class NoDocsDriverFactory(DriverFactory):
    """Hujjat yuklamagan haydovchi — tasdiqlab bo'lmaydi."""

    is_active = False
    is_online = False
    license_photo = None
    tech_passport_photo = None


class TariffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tariff

    name = factory.Sequence(lambda n: f"Tarif {n}")
    name_uz = factory.LazyAttribute(lambda o: o.name)
    base_fare = 5000
    per_km = 2000
    per_minute = 500
    minimum_fare = 10000
    is_active = True


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    client = factory.SubFactory(ClientFactory)
    driver = None
    tariff = factory.SubFactory(TariffFactory)
    status = OrderStatus.PENDING
    from_address = "Chilonzor 5-kvartal"
    from_location = factory.LazyFunction(lambda: point(41.2856, 69.2034))
    to_address = "Yunusobod 12-kvartal"
    to_location = factory.LazyFunction(lambda: point(41.3600, 69.2890))
    estimated_price = 25000
    distance_km = 8.5
    duration_min = 20


class CompletedOrderFactory(OrderFactory):
    status = OrderStatus.COMPLETED
    driver = factory.SubFactory(DriverFactory)
    final_price = 25000
    completed_at = factory.Faker("date_time_this_month", tzinfo=None)


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    amount = factory.LazyAttribute(
        lambda o: o.order.final_price or o.order.estimated_price
    )
    method = "click"
    status = PaymentState.PENDING


class HeavyRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HeavyEquipmentRequest

    category = "earth"
    items = factory.LazyFunction(lambda: [{"name": "Ekskavator", "quantity": 1}])
    address = "Sergeli tumani"
    start_date = "2026-09-01"
    duration_days = 2
    contact_name = "Olim Toshev"
    contact_phone = factory.Sequence(lambda n: f"+99891{n:07d}")


class WeddingRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WeddingRequest

    car_brand = "Chevrolet Malibu"
    car_count = 3
    decoration_type = "flowers"
    address = "Mirzo Ulug'bek tumani"
    date = "2026-09-15"
    duration_hours = 4
    contact_name = "Nodir Karimov"
    contact_phone = factory.Sequence(lambda n: f"+99893{n:07d}")


class ReviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Review

    order = factory.SubFactory(CompletedOrderFactory)
    author = factory.SelfAttribute("order.client")
    kind = ReviewKind.CLIENT_TO_DRIVER
    rating = 5
    comment = "Yaxshi haydovchi"
