"""Test models for Django."""

from django.db import models


class Product(models.Model):
    """Test Product model."""
    
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.IntegerField()
    likes = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'products'
        ordering = ['id']
