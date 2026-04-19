from rest_framework import serializers
from core.models import Image, Notification
from interactions.models import Booking


class ImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return obj.image.url
        return None
    class Meta:
        model = Image
        fields = ['id', 'url']
    

class Notificationserializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.model', read_only=True)
    '''
    targetObject = serializers.SerializerMethodField()

    def get_targetObject(self, obj):
        from interactions.serializers import BookingSerializer
        target_object = obj.target_object
        if target_object and isinstance(target_object, Booking):
            return BookingSerializer(target_object, context=self.context).data
        return None
    '''
    class Meta:
        model = Notification
        fields = "__all__"
