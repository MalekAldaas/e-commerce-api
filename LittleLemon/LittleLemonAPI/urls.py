from django.urls import path
from .views import (
    MenuItemListView,
    MenuItemDetailView,
    ManagerGroupView,
    ManagerGroupDetailView,
    DeliveryCrewGroupView,
    DeliveryCrewGroupDetailView,
    CartMenuItemView,
    OrderListView,
    OrderDetailView,
    AllUsersWithGroupsView,
)

urlpatterns = [
    path('menu-items', MenuItemListView.as_view(), name = 'menu-item-list'),
    path('menu-items/<int:pk>', MenuItemDetailView.as_view(), name='menu-item-detail'),
    path('groups/manager/users', ManagerGroupView.as_view(), name = 'manager-list'),
    path('groups/manager/users/<int:user_id>', ManagerGroupDetailView.as_view(), name='manager-detail'),
    path('groups/delivery-crew/users', DeliveryCrewGroupView.as_view(), name = 'deliver_crew-list'),
    path('groups/delivery-crew/users/<int:user_id>', DeliveryCrewGroupDetailView.as_view(),name='deliver_crew-detail'),
    path('groups/users', AllUsersWithGroupsView.as_view(), name="users-list"),
    path('cart/menu-items', CartMenuItemView.as_view(), name='cart-menu-items'), 
    path('orders', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>', OrderDetailView.as_view(), name='order-detail'),
]
