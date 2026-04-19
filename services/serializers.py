from interactions.models import HistoEtatBooking
from services.exceptions import ServiceItemCantBeDeletedException
from services.models import Domain, Service, ServiceItem, WorkTime
from rest_framework import serializers
from django.db import transaction
import logging
from users.models import Artist

logger = logging.getLogger(__name__)

class WorkTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkTime
        fields = "__all__"

class DomainSerializer(serializers.ModelSerializer):
    image = serializers.CharField()

    class Meta:
        model = Domain
        fields = "__all__"

class ServiceItemSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = ServiceItem
        fields = ["id", "name", "price"]

class ServiceSerializer(serializers.ModelSerializer):
    items = ServiceItemSerializer(many=True)
    domain = DomainSerializer(read_only=True)
    work_time = WorkTimeSerializer()
    domain_id = serializers.PrimaryKeyRelatedField(
        queryset=Domain.objects.all(), source='domain', write_only=True
    )

    class Meta:
        model = Service
        fields = ["domain_id", "name", "description", "work_time", "exp_years", "items", "domain"]

    @transaction.atomic
    def create(self, validated_data):
        artisan: Artist = self.context['request'].user.artist
        if hasattr(artisan, 'service'):
            raise serializers.ValidationError("Artist already has a service")
        items_data = validated_data.pop('items')
        work_time_data = validated_data.pop('work_time')
        work_time = WorkTime.objects.create(**work_time_data)
        service = Service.objects.create(
            artist=artisan,
            work_time=work_time,
            **validated_data
        )
        for item in items_data:
            ServiceItem.objects.create(service=service, **item)
        logger.info(f"Service '{service.name}' created by artist {artisan.id}")
        return service

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        work_time_data = validated_data.pop('work_time', None)

        # --- update main fields ---
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=validated_data.keys())

        # --- handle work_time (OneToOne nullable) ---
        if work_time_data is not None:
            if instance.work_time:
                for attr, value in work_time_data.items():
                    setattr(instance.work_time, attr, value)
                instance.work_time.save()
            else:
                instance.work_time = WorkTime.objects.create(**work_time_data)
                instance.save(update_fields=['work_time'])

        # --- sync items ---
        if items_data is not None:
            existing_items = {item.id: item for item in instance.items.all()}
            received_ids = set()

            for item_dict in items_data:
                item_id = item_dict.get('id')
                if item_id and item_id in existing_items:
                    item_obj = existing_items[item_id]
                    for attr, value in item_dict.items():
                        if attr != 'id':  # don't overwrite id
                            setattr(item_obj, attr, value)
                    item_obj.save()
                    received_ids.add(item_id)
                    logger.info(f"ServiceItem '{item_obj.name}' (id: {item_obj.id}) updated for service {instance.id}")
                else:
                    # new item
                    ServiceItem.objects.create(service=instance, **item_dict)

            # Delete items not included in update
            to_delete = [item for id_, item in existing_items.items() if id_ not in received_ids]
            for item in to_delete:
                if item.bookings.exists() and not item.bookings.filter(
                    status_history__status=HistoEtatBooking.COMPLETED_CHOICE
                ).exists():
                    logger.info(f"ServiceItem '{item.name}' (id: {item.id}) cannot be deleted because it has a non-completed booking")
                    raise ServiceItemCantBeDeletedException()
                
                logger.info(f"Deleting ServiceItem '{item.name}' (id: {item.id}) from service {instance.id}")
                item.delete()

        return instance
