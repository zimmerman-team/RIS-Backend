from rest_framework import serializers, exceptions
from favorite.models import Favorite
from generics.models import CombinedItem
from generics.serializers import CombinedSerializer


class favorite_item_serializer(serializers.ModelSerializer):
    class Meta:
        model = CombinedItem
        fields = ('item_id', 'item_type', 'name')


class FavoriteSerializer(serializers.ModelSerializer):
    item = CombinedSerializer(many=False, read_only=True)

    def __init__(self, *args, **kwargs):
        super(serializers.ModelSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context', None)
        if context:
            self.fields['item'] = CombinedSerializer(context=self.context)

    class Meta:
        model = Favorite
        fields = ('id', 'item', 'created_at')


class FavoriteExists(exceptions.APIException):
    status_code = 403
    default_detail = 'Item is al toegevoegd aan favorieten.'


class FavoriteAddSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'item', 'created_at')

    def validate(self, data):
        user = self.context.get('request').user
        isInFavorites = Favorite.objects.filter(owner=user, item=data['item'])

        if isInFavorites:
            raise FavoriteExists

        return data

    def create(self, validated_data):
        user = self.context.get('request').user
        favorite = Favorite.objects.create(owner=user, **validated_data)
        return favorite
