from django.urls import path

from portfolio.views import PortfolioItemView, PortfolioItemDetailView

urlpatterns = [
    path('items', PortfolioItemView.as_view(), name='manage_portfolio'),
    path('items/<int:pk>', PortfolioItemDetailView.as_view(), name='edit_portfolio_item'),
]
