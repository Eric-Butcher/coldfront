# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import datetime

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords
import decimal


# class AttributeType(TimeStampedModel):
#     """An attribute type indicates the data type of the attribute. Examples include Date, Float, Int, Text, and Yes/No.

#     Attributes:
#         name (str): name of attribute data type
#     """

#     name = models.CharField(max_length=128, unique=True)

#     def __str__(self):
#         return self.name

#     class Meta:
#         ordering = [
#             "name",
#         ]
class FundamentalType(models.IntegerChoices):
    """
    Defines the fundamental types supported by FundamentalValueModel 
    as well as functionality to convert between the Python typed valued
    and the way the value will be stored (as text) in the database.
    """
    INT = 1
    BOOL = 2
    FLOAT = 3
    DECIMAL = 4
    STR = 5
    DATETIME = 6

    @classmethod
    def fundamental_type_to_python_type(cls, fundamental_type: int) -> type:
        if not isinstance(fundamental_type, int):
            raise TypeError("fundamental_type must be an int")
        
        if fundamental_type == cls.INT.value:
            return int
        elif fundamental_type == cls.BOOL.value:
            return bool
        elif fundamental_type == cls.FLOAT.value:
            return float
        elif fundamental_type == cls.DECIMAL.value:
            return decimal
        elif fundamental_type == cls.STR.value:
            return str
        elif fundamental_type == cls.DATETIME.value:
            return datetime
        
        raise ValueError(f"fundamental_type of {fundamental_type} is not supported by {cls.__name__}.")
        

    @classmethod
    def python_type_to_fundamental_type(cls, type_of_object: type) -> int:
        if type(type_of_object) != type:
            raise TypeError("type_of_object must be a type.")

        if type_of_object == int:
            return cls.INT.value
        elif type_of_object == bool:
            return cls.BOOL.value
        elif type_of_object == float:
            return cls.FLOAT.value
        elif type_of_object == decimal:
            return cls.DECIMAL.value
        elif type_of_object == str:
            return cls.STR.value
        elif type_of_object == datetime:
            return cls.DATETIME.value
        
        raise ValueError(f"Type is not supported by {cls.__name__}.")


# class FundamentalValueModel(models.Model):
#     """"""

        
#     class FundamentalValueQuerySet(models.QuerySet):
#         if 

#     class FundamentalValueModelManager(models.Manager):
#         def get_queryset(self) -> models.QuerySet:
#             return super().get_queryset()
    

#     fundamental_type = models.IntegerField(choices=FundamentalType.choices, null=False)
#     value = models.TextField() # the raw value
#     default_objects = models.Manager()
#     fundamental_objects = 


class ResourceClassification(TimeStampedModel):
    """A model used to dictate classifications of resources.

    Attributes:
        name (str): name of resource type
        description (str): description of resource type
    """


    class ResourceTypeManager(models.Manager):
        def get_by_natural_key(self, name):
            return self.get(name=name)

    name = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=255)
    history = HistoricalRecords()
    objects = ResourceTypeManager()

    @property
    def active_count(self):
        """
        Returns:
            int: the number of active resources of that type
        """

        return ResourceAttribute.objects.filter(resource__resource_type__name=self.name, value="Active").count()

    @property
    def inactive_count(self):
        """
        Returns:
            int: the number of inactive resources of that type
        """

        return ResourceAttribute.objects.filter(resource__resource_type__name=self.name, value="Inactive").count()

    def __str__(self):
        return self.name

    def natural_key(self):
        return [self.name]


class ResourceAttributeType(TimeStampedModel):
    """A resource attribute type indicates the type of the attribute. Examples include slurm_specs and slurm_cluster.

    Attributes:
        attribute_type (AttributeType): indicates the AttributeType of the attribute
        name (str): name of resource attribute type
        is_required (bool): indicates whether or not the attribute is required
        is_value_unique (bool): indicates whether or not the value is unique

    Note: the is_unique_per_resource field is rarely used, hence documentation does not exist.
    """

    fundamental_type = models.IntegerField(choices=FundamentalType.choices)
    name = models.CharField(max_length=128)
    is_required = models.BooleanField(default=False)
    is_unique_per_resource = models.BooleanField(default=False)
    is_value_unique = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return self.name



class Resource(TimeStampedModel):
    """A resource is something a center maintains and provides access to for the community. Examples include Budgetstorage, Server, and Software License.

    Attributes:
        parent_resource (Resource): used for the Cluster Partition resource type as these partitions fall under a main cluster
        resource_type (ResourceType): the type of resource (Cluster, Storage, etc.)
        name (str): name of resource
        description (str): description of what the resource does and is used for
        is_available (bool): indicates whether or not the resource is available for users to request an allocation for
        is_public (bool):  indicates whether or not users can see the resource
        requires_payment (bool): indicates whether or not users have to pay to use this resource
        allowed_groups (Group): uses the Django Group model to allow certain user groups to request the resource
        allowed_users (User): links Django Users that are allowed to request the resource to the resource
    """

    class Meta(TimeStampedModel.Meta):
        ordering = [
            "name",
        ]

    class ResourceManager(models.Manager):
        def get_by_natural_key(self, name):
            return self.get(name=name)

    parent_resource = models.ForeignKey("self", on_delete=models.CASCADE, blank=True, null=True)
    resource_classification = models.ForeignKey(ResourceClassification, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField()
    is_available = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    is_allocatable = models.BooleanField(default=True)
    requires_payment = models.BooleanField(default=False)
    allowed_groups = models.ManyToManyField(Group, blank=True)
    allowed_users = models.ManyToManyField(User, blank=True)
    linked_resources = models.ManyToManyField("self", blank=True)
    history = HistoricalRecords()
    objects = ResourceManager()

    def get_missing_resource_attributes(self, required=False):
        """
        Params:
            required (bool): indicates whether or not to get only the missing resource attributes that are required (if True, get only required missing attributes; else, get required and non-required missing attributes)

        Returns:
            list[ResourceAttribute]: a list of resource attributes that do not already exist for this resource
        """

        if required:
            resource_attributes = ResourceAttributeType.objects.filter(resource_type=self.resource_classification, required=True)
        else:
            resource_attributes = ResourceAttributeType.objects.filter(resource_type=self.resource_classification)

        missing_resource_attributes = []

        for attribute in resource_attributes:
            if not ResourceAttribute.objects.filter(resource=self, resource_attribute_type=attribute).exists():
                missing_resource_attributes.append(attribute)
        return missing_resource_attributes

    @property
    def status(self):
        """
        Returns:
            str: the status of the resource
        """

        return ResourceAttribute.objects.get(resource=self, resource_attribute_type__attribute="Status").value


    def __str__(self):
        return "%s (%s)" % (self.name, self.resource_classification.name)

    def natural_key(self):
        return [self.name]


class ResourceAttribute(TimeStampedModel):
    """A resource attribute class links a resource attribute type and a resource.

    Attributes:
        resource_attribute_type (ResourceAttributeType): resource attribute type to link
        resource (Resource): resource to link
        value (str): value of the resource attribute
    """

    resource_attribute_type = models.ForeignKey(ResourceAttributeType, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    value = models.TextField()
    history = HistoricalRecords()

    def clean(self):
        """Validates the resource and raises errors if the resource is invalid."""
        expected_value_type = self.resource_attribute_type.fundamental_type.
        .name.strip()

        if expected_value_type == "Int" and not self.value.isdigit():
            raise ValidationError('Invalid Value "%s". Value must be an integer.' % (self.value))
        elif expected_value_type == "Active/Inactive" and self.value not in ["Active", "Inactive"]:
            raise ValidationError('Invalid Value "%s". Allowed inputs are "Active" or "Inactive".' % (self.value))
        elif expected_value_type == "Public/Private" and self.value not in ["Public", "Private"]:
            raise ValidationError('Invalid Value "%s". Allowed inputs are "Public" or "Private".' % (self.value))
        elif expected_value_type == "Date":
            try:
                datetime.strptime(self.value.strip(), "%m/%d/%Y")
            except ValueError:
                raise ValidationError('Invalid Value "%s". Date must be in format MM/DD/YYYY' % (self.value))

    def __str__(self):
        return "%s: %s (%s)" % (self.resource_attribute_type, self.value, self.resource)



    class Meta:
        unique_together = ("resource_attribute_type", "resource")
