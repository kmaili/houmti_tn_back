from rest_framework import serializers
from core.models import Image
from core.serializers import ImageSerializer
from portfolio.models import Portfolio, PortfolioItem
from django.db import transaction

class PortfolioItemSerializer(serializers.ModelSerializer):
    images_upload = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = PortfolioItem
        fields = ["id", "name", "description", "visible", "images", "images_upload", "created_at", "updated_at"]

    @transaction.atomic
    def create(self, validated_data):
        # On extrait les fichiers du champ write_only
        images_files = validated_data.pop('images_upload', [])
        item = PortfolioItem.objects.create(**validated_data)
        
        for img_file in images_files:
            Image.objects.create(portfolio_item=item, image=img_file)
        
        return item
    
    @transaction.atomic
    def update(self, instance, validated_data):
        images_files = validated_data.pop('images_upload', [])
        item = super().update(instance, validated_data)
        
        item.images.all().delete()
        for img_file in images_files:
            Image.objects.create(portfolio_item=item, image=img_file)
        
        return item

class PortfolioSerializer(serializers.ModelSerializer):
    items = PortfolioItemSerializer(many=True)
    nb_views = serializers.ReadOnlyField()
    date_creation = serializers.ReadOnlyField()

    class Meta:
        model = Portfolio
        fields = "__all__"
    

