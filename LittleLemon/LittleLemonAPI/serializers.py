from rest_framework import serializers
from .models import MenuItem, Cart, Order, OrderItem

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']
        read_only_fields = ['unit_price', 'price']

    def create(self, validated_data):
        user = self.context['request'].user
        menuitem = validated_data['menuitem']
        quantity = validated_data['quantity']
        unit_price = menuitem.price
        total_price = unit_price * quantity

        # Prevent duplicate entries: update quantity if exists
        cart_item, created = Cart.objects.update_or_create(
            user=user,
            menuitem=menuitem,
            defaults={
                'quantity': quantity,
                'unit_price': unit_price,
                'price': total_price
            }
        )
        return cart_item
    
    

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = serializers.StringRelatedField()
    
    class Meta:
        model = OrderItem
        fields = (
            'id',
            'menuitem',
            'quantity',
            'unit_price',
        )
        
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.HiddenField(
        default = serializers.CurrentUserDefault()
    )
    total = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )
    date = serializers.DateField(read_only=True)
    status = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'status',
            'total',
            'date',
            'items',
        )