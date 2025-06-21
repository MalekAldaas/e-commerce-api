from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import MenuItem, Cart, OrderItem, Order
from .serializers import MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from .permissions import RolePermission
from rest_framework.serializers import ValidationError
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend



User = get_user_model()

def get_group(name):
    return Group.objects.get(name=name)


class MenuItemListView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [RolePermission]
    
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter
    ]
    filterset_fields = ['category', 'price']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price']

    permission_map = {
        'GET': ['manager', 'deliver_crew', 'customer'],
        'POST': ['manager'],
    }

class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [RolePermission]

    permission_map = {
        'GET': ['manager', 'deliver_crew', 'customer'],
        'PUT': ['manager'],
        'PATCH': ['manager'],
        'DELETE': ['manager'],
    }

class DeliveryCrewGroupView(APIView):
    permission_classes = [RolePermission]

    permission_map = {
        'GET': ['manager'],
        'POST': ['manager'],
    }

    def get(self, request):
        crew = User.objects.filter(groups__name='deliver_crew')
        data = [{'id': user.id, 'username': user.username} for user in crew]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            group = get_group('deliver_crew')
            group.user_set.add(user)
            return Response({'message': 'User added to delivery crew'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class DeliveryCrewGroupDetailView(APIView):
    permission_classes = [RolePermission]

    permission_map = {
        'DELETE': ['manager'],
    }

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            group = get_group('deliver_crew')
            group.user_set.remove(user)
            return Response({'message': 'User removed from delivery crew'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class ManagerGroupView(APIView):
    permission_classes = [RolePermission]
    permission_map = {
        'GET' : ["manager"],
        'POST': ["manager"],
    }

    def get(self, request):
        managers = User.objects.filter(groups__name='manager')
        data = [{'id': user.id, 'username': user.username} for user in managers]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            group = get_group('manager')
            group.user_set.add(user)
            return Response({'message': 'User added to manager group'}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class ManagerGroupDetailView(APIView):
    permission_classes = [RolePermission]
    permission_map = {
        'DELETE': ["manager"],
    }
    
    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            group = get_group('manager')
            group.user_set.remove(user)
            return Response({'message': 'User removed from manager group'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        
class CartMenuItemView(APIView):
    permission_classes = [RolePermission]

    permission_map = {
        'GET': ['customer'],
        'POST': ['customer'],
        'DELETE': ['customer'],
    }

    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CartSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        deleted_count, _ = Cart.objects.filter(user=request.user).delete()
        return Response({'message': f'{deleted_count} cart item(s) deleted.'}, status=status.HTTP_200_OK)
    

class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [RolePermission]
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'date']
    search_fields = ['user__username']
    ordering_fields = ['date', 'total']

    permission_map = {
        'GET': ['manager', 'customer', 'deliver_crew'],
        'POST': ['customer'],
    }

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='deliver_crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:  # customer
            return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            raise ValidationError("Cart is empty. Cannot create order.")

        total = sum(item.price for item in cart_items)
        order = serializer.save(user=user, total=total, date=timezone.now().date())

        # Create order items from cart items
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price
            )

        # Clear cart after order creation
        cart_items.delete()


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [RolePermission]

    permission_map = {
        'GET': ['manager', 'customer', 'deliver_crew'],
        'PUT': ['manager'],
        'PATCH': ['manager', 'deliver_crew'],
        'DELETE': ['manager'],
    }

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='deliver_crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:  # customer
            return Order.objects.filter(user=user)

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
        return obj

    def update(self, request, *args, **kwargs):
        user = request.user
        order = self.get_object()
        data = request.data.copy()

        # manager can update delivery_crew and status
        if user.groups.filter(name='manager').exists():
            # Validate delivery_crew user if provided
            delivery_crew_id = data.get('delivery_crew')
            if delivery_crew_id:
                try:
                    delivery_crew_user = User.objects.get(id=delivery_crew_id)
                    if not delivery_crew_user.groups.filter(name='deliver_crew').exists():
                        return Response({'error': 'User is not delivery crew'}, status=status.HTTP_400_BAD_REQUEST)
                except User.DoesNotExist:
                    return Response({'error': 'delivery crew user not found'}, status=status.HTTP_400_BAD_REQUEST)
            return super().update(request, *args, **kwargs)

        # delivery crew can only PATCH status (0 or 1)
        if user.groups.filter(name='deliver_crew').exists():
            if 'status' in data:
                # Only allow status update, no other fields
                allowed_statuses = [0, 1, False, True]  # boolean or int
                status_val = data.get('status')
                if status_val not in allowed_statuses and str(status_val).lower() not in ['true', 'false']:
                    return Response({'error': 'Invalid status value'}, status=status.HTTP_400_BAD_REQUEST)
                order.status = bool(int(status_val)) if isinstance(status_val, str) else bool(status_val)
                order.save()
                serializer = self.get_serializer(order)
                return Response(serializer.data)
            else:
                return Response({'error': 'Only status update allowed'}, status=status.HTTP_403_FORBIDDEN)

        # customers cannot update order
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)


class AllUsersWithGroupsView(APIView):
    permission_classes = [RolePermission]
    permission_map = {
        'GET': ['manager'],  # Only manager can access
    }

    def get(self, request):
        users = User.objects.all()
        data = []
        for user in users:
            groups = [g.name for g in user.groups.all()]
            data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'groups': groups or ['customer']
            })
        return Response(data, status=status.HTTP_200_OK)
